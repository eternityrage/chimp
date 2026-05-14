import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Group Chats Are War Zones — Chimp Unfiltered",
        "People Who Say 'I'm Just Built Different'",
        "The Loud Chewer Epidemic — Chimp Unfiltered",
        "Gym Bros Are a Different Breed",
        "Why Nobody Knows How to Merge Lanes Anymore",
        "Overthinkers Anonymous — Chimp Unfiltered",
        "People Who Make Their Whole Personality a Sport Team",
        "The Art of Ghosting and Coming Back Like Nothing Happened",
        "Why Every Office Has That One Microwave Villain",
        "Adults Who Still Can't Handle Vegetables",
        "The Mystery of People Who Love Small Talk",
        "Drivers Who Treat Turn Signals as Optional",
        "People Who Film Themselves Crying in Public",
        "The Cult of Morning People — Exposed",
        "Why Everyone Suddenly Thinks They're a Therapist",
    ]

    fallback_descriptions = [
        "Group chats are the most dangerous places on Earth. 387 unread messages, voice note guys, meme addicts at 3 AM, and that one cousin who disappears for six months then returns with a single laughing emoji. BROTHER it's digital survival out there. Drop a 🔥 if your group chat is chaos too. Comment which character type YOU are. Follow Chimp Unfiltered for more rants! #chimpunfiltered #groupchats #comedy #podcast #relatable #funny #rant #millennialhumor #digitalchaos #messaging #memes #voicenotes",
        "Anytime somebody says 'I'm just built different' — prepare for nonsense. A dude eats one salad and suddenly he's a motivational speaker. BROTHER you folded under medium pressure last Thursday. Relax. From gym bros who film their morning routine like a nature documentary to LinkedIn gurus who hate weekends — we call out the exaggerated hustle culture. Like if you know one of these people. Comment the most 'built different' thing you've ever heard. Subscribe for more! #chimpunfiltered #builtdifferent #grindset #gymbros #comedy #podcast #satire #funny #relatable #motivation",
        "Why does the office always have THAT person who microwaves fish? And why do loud chewers think nobody can hear them? BROTHER we can hear your soul through your molars. From public transport etiquette violations to people who block the entire aisle with their shopping cart — we're calling out society's worst offenders. Drop a 🐟 if someone has microwaved fish near you. Tag the loud chewer in your life (don't actually do that). Follow Chimp Unfiltered! #chimpunfiltered #petpeeves #office #loudchewing #comedy #podcast #rant #relatable #annoying #publicetiquette",
        "Gym culture is a wild ride. You got guys screaming while lifting 5kg dumbbells. People filming every single set like they're in a documentary. That one person who hogs the squat rack to do bicep curls. And don't get me started on the gym bro who walks around shirtless for 45 minutes after his workout. BROTHER put the shirt on, we get it. Like if you've seen this at your gym. Comment the most annoying gym behavior you've witnessed. Hit follow for more! #chimpunfiltered #gym #gymbros #fitness #comedy #podcast #rant #relatable #gymculture #workout #satire",
        "Nobody knows how to merge lanes anymore and I'm tired of pretending they do. It's every driver for themselves out there. Turn signals? Optional. Speed limits? Suggestions. And why does everyone drive 20 under in the left lane like they're escorting a parade? BROTHER MOVE. From road rage to roundabout confusion — we're covering all of it. Drop a 🚗 if you've almost lost it on the highway today. Comment your worst driving pet peeve. Follow for weekly rants! #chimpunfiltered #driving #traffic #roads #comedy #podcast #rant #car #commute #relatable #satire",
        "Overthinking is a full-time job with no salary. You send one text and suddenly you're analyzing their typing bubbles for hidden meanings. They said 'k' instead of 'okay' — is everything fine? BROTHER they're fine. Meanwhile you've planned your entire apology speech for something that hasn't happened. From replaying conversations in the shower to lying awake at 3 AM remembering that embarrassing thing from 2014 — this is for all the overthinkers. Like if this hit too close to home. Comment what keeps YOU up at night. Subscribe! #chimpunfiltered #overthinking #anxiety #relatable #comedy #podcast #rant #mentalhealth #thoughts #nightthoughts",
        "Some people make watching sports their entire personality. Their profile picture is them in jersey. Their bio mentions their team. Every conversation circles back to 'the game.' BROTHER do you even know your cousin's birthday? We're not anti-sports, we're anti-IDENTITY-CRISIS-via-sports-team. And why do fans act like they personally contributed to the win? You were on the couch eating chips. You didn't make that touchdown. Drop a 🏈 if you know someone like this. Tag them (they probably won't see it, they're watching highlights). Join us! #chimpunfiltered #sports #fans #comedy #podcast #satire #relatable #rant #football #sportsculture",
        "Ghosting is wild. You're talking to someone daily, then POOF — gone like a magician who retired. Then six months later they pop up with 'hey stranger hope you're well' like they were in a coma. BROTHER I'M NOT A BOOKMARK. You can't pause me and come back later. From the slow fade to the full disappearance — we're breaking down modern dating's worst habit. Like if you've been ghosted. Comment how long it took them to come back. Follow Chimp Unfiltered for more! #chimpunfiltered #ghosting #dating #relationships #comedy #podcast #rant #relatable #modernlove #datingculture",
        "Every office has that one microwave villain. You know who you are. You heat up fish. You set the timer for 10 minutes for soup. You leave the microwave looking like a crime scene. BROTHER it's a microwave not a war zone. And why does nobody clean the break room fridge? There's a Tupperware in there from 2019 that has achieved sentience. From passive-aggressive sticky notes to the person who takes the last coffee without making more — office chaos is real. Drop a ☕ if you relate. Comment your office's worst offender. Chimp Unfiltered out! #chimpunfiltered #office #work #microwave #comedy #podcast #rant #relatable #worklife #corporate",
        "Adults who can't eat vegetables without making it everyone's problem. BROTHER it's a carrot not a betrayal. You see one leaf on your burger and suddenly you're a food detective picking it apart piece by piece. 'I don't eat green things.' My guy you're 34. And why do picky eaters act proud of it like it's a personality trait? 'I only eat chicken nuggets and fries.' Like if you know a grown-up who eats like this. Comment the most ridiculous food take you've heard. Follow for more! #chimpunfiltered #food #pickyeaters #adults #comedy #podcast #rant #vegetables #relatable #satire",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "loud, ranty, and hilarious — like a friend venting at a bar about society's nonsense",
        "sarcastic and witty — mock modern absurdities with sharp humor",
        "over-the-top and dramatic — act like every minor annoyance is a global crisis",
        "deadpan and observational — point out everyday nonsense with dry comedy",
        "chaotic and unhinged — energy of someone who hasn't slept but has opinions",
        "mock-serious and satire — treat ridiculous things with extreme fake seriousness",
        "playful roasting — go in hard on bad behavior, but keep it funny",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and engaging title and description for a short comedy rant video "
        f"for the channel 'Chimp Unfiltered'. "
        f"The channel is a funny, satirical comedy podcast that rants about everyday modern life — "
        f"group chats, gym culture, bad drivers, picky eaters, overthinkers, office nonsense, "
        f"and all the ridiculous things people do. "
        f"Speak as the host — loud, unfiltered, calling people 'BROTHER' a lot, energetically ranting. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), hilarious, and unhinged. "
        f"IMPORTANT POLICY RULES — You MUST follow these: "
        f"- Do NOT use slurs, profanity, or hate speech "
        f"- Do NOT attack any person or group based on race, ethnicity, religion, gender, sexual orientation, or disability "
        f"- Do NOT incite violence or harassment "
        f"- Do NOT spread medical or political misinformation "
        f"- Do NOT mock mental health conditions "
        f"- Keep it lighthearted observational comedy — roast the BEHAVIOR, not the person "
        f"- Avoid terms like 'lunatic', 'crazy', 'insane', 'psycho', or any ableist language "
        f"Include engagement calls-to-action such as: "
        f"- Like if you relate! "
        f"- Comment your worst experience! "
        f"- Tag someone who needs to hear this! "
        f"- Follow Chimp Unfiltered for more rants! "
        f"Include relevant hashtags in ALL LOWERCASE such as #chimpunfiltered #comedy #podcast #rant #funny #satire #relatable #millennialhumor #lol #viral. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    blocked_words = ["lunatic", "crazy", "insane", "psycho", "mentally ill", "retard", "spastic", "deranged", "maniac", "nazi", "stupid", "idiot", "moron", "sociopath"]

    def is_policy_compliant(text):
        lowered = text.lower()
        for word in blocked_words:
            if word in lowered:
                print(f"⚠️  Policy flag: blocked word '{word}' found in generated content. Using fallback instead.")
                return False
        return True

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        ai_title = result.get("title", "")
        ai_desc = result.get("description", "")

        if ai_title and ai_desc and is_policy_compliant(ai_title) and is_policy_compliant(ai_desc):
            return ai_title, ai_desc
        else:
            print("⚠️  AI caption flagged by policy filter. Using fallback.")
            return random.choice(fallback_titles), random.choice(fallback_descriptions)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["chimp unfiltered", "comedy podcast", "funny rants", "satire", "stand up comedy", "relatable humor", "millennial humor", "podcast clips", "comedian", "viral comedy", "life rants", "funny moments", "hilarious", "comedy shorts", "brother"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
