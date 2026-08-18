# -*- coding: utf-8 -*-
"""FitPulse exercise library - 42 exercises with verified YouTube demo videos.
Image = YouTube thumbnail (https://i.ytimg.com/vi/{id}/hqdefault.jpg), video = embed.
Fallback in templates handles missing network gracefully."""

EXERCISES = [
    # (name, category, muscle, equipment, video_id, difficulty, sets, reps, instructions)
    ("Push-Up", "Strength", "Chest", "Bodyweight", "IODxDxX7oi4", "Beginner", 3, "10-15",
     "Hands shoulder-width apart, body in straight line. Lower chest to floor, push back up."),
    ("Bench Press", "Strength", "Chest", "Barbell", "rT7DgCr-3pg", "Intermediate", 4, "8-10",
     "Lie on bench, lower bar to mid-chest, press up with control. Keep feet planted."),
    ("Incline Dumbbell Press", "Strength", "Chest", "Dumbbell", "8iPEnn-ltC8", "Intermediate", 3, "10-12",
     "Set bench at 30-45 deg, press dumbbells up from shoulders, lower slowly."),
    ("Dumbbell Fly", "Strength", "Chest", "Dumbbell", "eozdVDA78K0", "Intermediate", 3, "10-12",
     "Lie on bench, arms open wide with slight bend, squeeze chest to bring weights together."),
    ("Chest Dip", "Strength", "Chest", "Bodyweight", "2z8JmcrW-As", "Intermediate", 3, "8-12",
     "Lean forward on parallel bars, lower until shoulders dip, press up."),
    ("Pull-Up", "Strength", "Back", "Bodyweight", "eGo4IYlbE5g", "Intermediate", 3, "6-10",
     "Hang from bar, pull chin above bar, lower slowly. Use band if needed."),
    ("Lat Pulldown", "Strength", "Back", "Machine", "CAwf7n6Luuc", "Beginner", 3, "10-12",
     "Grip wide bar, pull to upper chest, squeeze lats, return slowly."),
    ("Seated Cable Row", "Strength", "Back", "Cable", "GZbfZ033f74", "Beginner", 3, "10-12",
     "Sit tall, pull handle to stomach, squeeze shoulder blades, return slowly."),
    ("Bent-Over Row", "Strength", "Back", "Barbell", "T3N-TO4reLQ", "Intermediate", 4, "8-10",
     "Hinge forward with flat back, row bar to lower chest, lower under control."),
    ("One-Arm Dumbbell Row", "Strength", "Back", "Dumbbell", "pYcpY20QaE8", "Beginner", 3, "10-12",
     "Knee and hand on bench, pull dumbbell to hip, keep back flat."),
    ("Back Extension", "Strength", "Lower Back", "Bodyweight", "AbE5Q0ibscY", "Beginner", 3, "12-15",
     "On hyperextension bench, hinge down then raise torso to straight line."),
    ("Barbell Squat", "Strength", "Legs", "Barbell", "aclHkVaku9U", "Intermediate", 4, "8-12",
     "Bar on upper back, squat down to parallel, drive through heels to stand."),
    ("Goblet Squat", "Strength", "Legs", "Dumbbell", "aKq417Z8sLU", "Beginner", 3, "10-12",
     "Hold dumbbell at chest, squat deep keeping chest up, push through heels."),
    ("Walking Lunge", "Strength", "Legs", "Bodyweight", "QOVaHwm-Q6U", "Beginner", 3, "10 per leg",
     "Step forward, lower back knee near floor, push off to next step."),
    ("Leg Press", "Strength", "Legs", "Machine", "IZxyjW7MPJQ", "Beginner", 3, "10-12",
     "Feet on platform, lower until knees at 90 deg, press without locking knees."),
    ("Romanian Deadlift", "Strength", "Legs", "Barbell", "JCXUYuzwNrM", "Intermediate", 3, "8-10",
     "Hinge at hips with slight knee bend, slide bar down legs, squeeze glutes to stand."),
    ("Standing Calf Raise", "Strength", "Calves", "Bodyweight", "ndQc4mz4mBU", "Beginner", 4, "15-20",
     "Rise onto toes, pause at top, lower slowly for full stretch."),
    ("Glute Bridge", "Strength", "Glutes", "Bodyweight", "wPM8icPu6H8", "Beginner", 3, "12-15",
     "Lie on back, push hips up squeezing glutes, lower slowly."),
    ("Hip Thrust", "Strength", "Glutes", "Barbell", "SEdqd1n0cvg", "Intermediate", 4, "8-12",
     "Shoulders on bench, barbell over hips, thrust up squeezing glutes at top."),
    ("Overhead Press", "Strength", "Shoulders", "Barbell", "2yjwXTZQDDI", "Intermediate", 4, "6-8",
     "Press bar overhead from shoulders, keep core tight, lock out then lower."),
    ("Dumbbell Shoulder Press", "Strength", "Shoulders", "Dumbbell", "qEwKCR5JCog", "Beginner", 3, "10-12",
     "Press dumbbells overhead from shoulders, avoid arching back."),
    ("Lateral Raise", "Strength", "Shoulders", "Dumbbell", "3VcKaXpzqRo", "Beginner", 3, "12-15",
     "Raise dumbbells out to sides to shoulder height with slight elbow bend."),
    ("Front Raise", "Strength", "Shoulders", "Dumbbell", "PUpv-TQR1eE", "Beginner", 3, "10-12",
     "Raise dumbbells in front to shoulder height, keep arms straight, lower slowly."),
    ("Rear Delt Fly", "Strength", "Shoulders", "Dumbbell", "B-aVuyhvLHU", "Beginner", 3, "12-15",
     "Hinge forward, open arms wide squeezing rear shoulders, control the return."),
    ("Barbell Curl", "Strength", "Biceps", "Barbell", "kwG2ipFRgfo", "Beginner", 3, "10-12",
     "Curl bar with elbows pinned to sides, squeeze at top, lower slowly."),
    ("Hammer Curl", "Strength", "Biceps", "Dumbbell", "Iz1kGNIfS3Y", "Beginner", 3, "10-12",
     "Neutral grip, curl dumbbells keeping elbows fixed at sides."),
    ("Tricep Dips", "Strength", "Triceps", "Bodyweight", "0326dy_-CzM", "Beginner", 3, "8-12",
     "Hands on bench behind, lower body until elbows at 90 deg, press up."),
    ("Tricep Pushdown", "Strength", "Triceps", "Cable", "2-LAMcpzODU", "Beginner", 3, "10-12",
     "Push cable bar down with elbows fixed, fully extend arms, return slowly."),
    ("Overhead Tricep Extension", "Strength", "Triceps", "Dumbbell", "EagczN3i3OY", "Beginner", 3, "10-12",
     "Hold dumbbell overhead, lower behind head bending elbows, extend back up."),
    ("Plank", "Core", "Core", "Bodyweight", "pSHjTRCQxIw", "Beginner", 3, "30-60 sec",
     "Forearms and toes on floor, body straight line, brace abs, breathe."),
    ("Crunch", "Core", "Core", "Bodyweight", "Xyd_fa5zoEU", "Beginner", 3, "15-20",
     "Lie on back, curl shoulders toward hips using abs, lower slowly."),
    ("Russian Twist", "Core", "Core", "Bodyweight", "wkD8rjkodUI", "Beginner", 3, "20 per side",
     "Sit leaned back, rotate torso side to side with feet off floor."),
    ("Lying Leg Raise", "Core", "Core", "Bodyweight", "9GyRfk7E86E", "Beginner", 3, "12-15",
     "Lie flat, lift straight legs to vertical keeping lower back down, lower slowly."),
    ("Mountain Climbers", "Core", "Core", "Bodyweight", "nmwgirgXLYM", "Intermediate", 3, "30 sec",
     "In plank position, drive knees to chest alternating fast."),
    ("Bicycle Crunch", "Core", "Core", "Bodyweight", "9FGilxCbdz8", "Intermediate", 3, "15 per side",
     "Pedal legs while bringing opposite elbow to knee, controlled rotation."),
    ("Jumping Jacks", "Cardio", "Cardio", "Bodyweight", "iSSAk4XCsRA", "Beginner", 3, "60 sec",
     "Jump feet out while arms overhead, then back together. Keep rhythm."),
    ("Burpees", "Cardio", "Cardio", "Bodyweight", "TU8QYVW0gDU", "Intermediate", 3, "10-15",
     "Squat down, kick to plank, push-up, jump feet in, leap up. Full body."),
    ("Jump Rope", "Cardio", "Cardio", "Jump Rope", "NkXDy8K-1jY", "Beginner", 3, "60 sec",
     "Swing rope over head, hop on balls of feet as rope passes."),
    ("High Knees", "Cardio", "Cardio", "Bodyweight", "m5UODKFL2Fs", "Beginner", 3, "30 sec",
     "Run in place driving knees up to hip height, pump arms."),
    ("Cat-Cow Stretch", "Yoga", "Spine", "Bodyweight", "y39PrKY_4JM", "Beginner", 3, "10 reps",
     "On hands and knees, alternate rounding and arching the spine with breath."),
    ("Child's Pose", "Yoga", "Back", "Bodyweight", "l0_RBfKFlz0", "Beginner", 2, "30 sec",
     "Kneel, sit back on heels, fold forward resting forehead on floor."),
    ("Cobra Stretch", "Yoga", "Chest/Back", "Bodyweight", "edQX9kGYmAk", "Beginner", 3, "10 reps",
     "Lie face down, press chest up keeping hips down, look up gently."),
]

CATEGORIES = ["Strength", "Cardio", "Yoga"]
MUSCLES = sorted({e[2] for e in EXERCISES})
EQUIPMENT = sorted({e[3] for e in EXERCISES})
DIFFICULTIES = ["Beginner", "Intermediate"]


def yt_thumb(video_id):
    return "https://i.ytimg.com/vi/%s/hqdefault.jpg" % video_id


def yt_embed(video_id):
    return "https://www.youtube.com/embed/%s?rel=0" % video_id


def yt_watch(video_id):
    return "https://www.youtube.com/watch?v=%s" % video_id


def rows():
    """Return list of dicts ready for DB insert."""
    out = []
    for (name, cat, muscle, equip, vid, diff, sets, reps, instr) in EXERCISES:
        out.append({
            "name": name, "category": cat, "muscle": muscle, "equipment": equip,
            "image_url": yt_thumb(vid), "video_url": yt_embed(vid),
            "difficulty": diff, "instructions": instr,
            "default_sets": sets, "default_reps": reps,
        })
    return out
