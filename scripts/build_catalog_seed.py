"""Builds seeds/fortunis8_catalog_seed.sql from the content below.
Authored by Hark. Content rules: evidence-informed behaviour change, no medical or
psychological claims, no guarantees, belief modes user-chosen, readings optional.
Run: python scripts/build_catalog_seed.py
"""
import json, os

GOALS = [
 ("business_wealth","Business & wealth mindset","کاروبار اور مالی سوچ","Clear financial priorities and consistent business actions."),
 ("study_exams","Study & exam preparation","پڑھائی اور امتحان کی تیاری","Focused study blocks and steady revision."),
 ("career_interview","Job & interview confidence","نوکری اور انٹرویو کا اعتماد","Prepared, confident career moves."),
 ("health_energy","Health & energy habits","صحت اور توانائی کی عادات","Small daily habits for movement, water and rest."),
 ("stress_calm","Stress reduction & calm","ذہنی دباؤ میں کمی اور سکون","Short regulation practices for calmer days."),
 ("relationships","Relationships","رشتے","Kinder, clearer connection with people who matter."),
 ("creativity","Creativity","تخلیقی صلاحیت","Regular making, idea capture and play."),
 ("discipline","Discipline","نظم و ضبط","Keeping small promises to yourself."),
 ("spiritual_reflection","Spiritual reflection","روحانی غور و فکر","Meaning, gratitude and inner reflection."),
 ("religious_routine","Religious routine","مذہبی معمول","Support for the routine of your own faith, as you define it."),
 ("confidence","Confidence","خود اعتمادی","Evidence-based self-belief through small wins."),
 ("life_transition","Life transition","زندگی کی تبدیلی","Steadiness through moves, endings and new starts."),
 ("sleep_recovery","Sleep & recovery","نیند اور آرام","Wind-down routines that support rest."),
]

MODES = [  # key, en, ur, description, requires_opt_in
 ("scientific","Scientific","سائنسی","Evidence-informed habit and attention practices.",False),
 ("mindfulness","Mindfulness","مائنڈفلنس","Breath, attention and present-moment awareness.",False),
 ("practical","Practical action","عملی قدم","Plans, checklists and one concrete step.",False),
 ("motivational","Motivational","حوصلہ افزا","Encouraging prompts and progress reminders.",False),
 ("visualization","Visualization","تصور","Imagining the next step clearly before taking it.",False),
 ("spiritual_reflection","Spiritual reflection","روحانی غور","Meaning, gratitude and reflection, without a specific doctrine.",True),
 ("religious_practice","Religious practice","مذہبی عمل","Reminders shaped around the user's own stated faith.",True),
 ("mixed","Mixed","ملا جلا","A blend of the modes the user selected.",False),
]

STATES = [
 ("stressed","Stressed","دباؤ میں"),("low_energy","Low energy","کم توانائی"),
 ("distracted","Distracted","بکھری توجہ"),("motivated","Motivated","پرجوش"),
 ("uncertain","Uncertain","غیر یقینی"),("calm","Calm","پرسکون"),
]

TRADITIONS = [
 ("none","No tradition","کوئی نہیں"),("islam","Islam","اسلام"),("christianity","Christianity","مسیحیت"),
 ("hinduism","Hinduism","ہندومت"),("sikhism","Sikhism","سکھ مت"),("buddhism","Buddhism","بدھ مت"),
 ("other","Other / personal","دیگر / ذاتی"),
]

# key, type, mode, seconds, goals, states, en_title, en_instr, ur_title, ur_instr, safety
R = [
 ("box_breath_4","breath","mindfulness",120,["stress_calm","study_exams","career_interview"],["stressed","distracted"],
  "Box breathing, 2 minutes","Breathe in for 4, hold 4, out 4, hold 4. Repeat 6 rounds. Then name one thing you will do next.",
  "باکس بریدنگ، 2 منٹ","4 گنتی سانس اندر، 4 روکیں، 4 باہر، 4 روکیں۔ 6 بار دہرائیں۔ پھر اگلا ایک کام طے کریں۔",
  "Stop if you feel dizzy and breathe normally."),
 ("long_exhale","breath","scientific",90,["stress_calm","sleep_recovery"],["stressed"],
  "Longer exhale","Inhale through the nose for 4, exhale slowly for 6 to 8. Ten rounds.",
  "لمبی سانس باہر","ناک سے 4 گنتی سانس لیں، 6 سے 8 گنتی آہستہ چھوڑیں۔ دس بار۔",
  "Stop if you feel lightheaded."),
 ("one_priority","practical_action","practical",180,["discipline","business_wealth","study_exams","career_interview"],["distracted","uncertain"],
  "One priority","Write the single task that would make today a win. Add when and where you will start it.",
  "ایک ترجیح","وہ ایک کام لکھیں جو آج کو کامیاب بنا دے۔ ساتھ لکھیں کب اور کہاں شروع کریں گے۔",None),
 ("if_then_plan","practical_action","scientific",180,["discipline","health_energy","study_exams"],["motivated","distracted"],
  "If-then plan","Complete: If it is [time/place], then I will [small action]. Keep the action under 5 minutes.",
  "اگر-تو منصوبہ","مکمل کریں: اگر [وقت/جگہ] ہو تو میں [چھوٹا کام] کروں گا۔ کام 5 منٹ سے کم رکھیں۔",None),
 ("focus_block_25","practical_action","scientific",1500,["study_exams","creativity","business_wealth"],["motivated"],
  "25-minute focus block","Silence your phone, set a 25-minute timer, work on one thing only. Note what you finished.",
  "25 منٹ کا فوکس","فون خاموش کریں، 25 منٹ کا ٹائمر لگائیں، صرف ایک کام کریں۔ آخر میں لکھیں کیا مکمل ہوا۔",None),
 ("active_recall","practical_action","scientific",600,["study_exams"],["calm","motivated"],
  "Active recall","Close your notes. Write everything you remember about one topic, then check and mark gaps.",
  "یاد سے دہرائی","نوٹس بند کریں۔ ایک موضوع کے بارے میں جو یاد ہے لکھیں، پھر چیک کر کے کمی نشان زد کریں۔",None),
 ("money_check","practical_action","practical",300,["business_wealth"],["uncertain"],
  "5-minute money check","Review yesterday's income and spending. Write one decision for today.",
  "5 منٹ مالی جائزہ","کل کی آمدن اور خرچ دیکھیں۔ آج کے لیے ایک فیصلہ لکھیں۔",
  "This is a reflection exercise, not financial advice."),
 ("customer_reachout","practical_action","motivational",600,["business_wealth","career_interview"],["motivated"],
  "One reach-out","Send one useful message to a customer, colleague or contact. Keep it short and specific.",
  "ایک رابطہ","کسی گاہک، ساتھی یا جاننے والے کو ایک مفید، مختصر پیغام بھیجیں۔",None),
 ("star_story","reflection","practical",420,["career_interview","confidence"],["uncertain"],
  "STAR story","Write one achievement as Situation, Task, Action, Result. Practise saying it aloud once.",
  "STAR کہانی","ایک کامیابی کو صورتحال، ذمہ داری، عمل، نتیجہ کی ترتیب سے لکھیں۔ ایک بار بلند آواز سے دہرائیں۔",None),
 ("evidence_list","reflection","scientific",240,["confidence","life_transition"],["uncertain","stressed"],
  "Evidence list","Write three things you handled well this month. Next to each, the skill it shows.",
  "ثبوت کی فہرست","اس مہینے کی تین چیزیں لکھیں جو آپ نے اچھی طرح سنبھالیں، اور ہر ایک کے ساتھ اس سے ظاہر ہونے والی صلاحیت۔",None),
 ("reframe_thought","reflection","scientific",300,["stress_calm","confidence"],["stressed","uncertain"],
  "Reframe one thought","Write a worrying thought. Ask: what is another way to see this? Write a balanced version.",
  "ایک خیال کو نئے زاویے سے","ایک پریشان کن خیال لکھیں۔ پوچھیں: اسے کیسے مختلف دیکھا جا سکتا ہے؟ متوازن صورت لکھیں۔",
  "If distress is persistent or severe, please talk to a qualified professional."),
 ("gratitude_three","reflection","spiritual_reflection",180,["spiritual_reflection","stress_calm","relationships"],["calm","low_energy"],
  "Three gratitudes","Write three specific things you are grateful for today and why each matters.",
  "تین شکر","آج کی تین خاص چیزیں لکھیں جن پر شکر گزار ہیں اور کیوں۔",None),
 ("evening_review","reflection","mixed",300,["discipline","spiritual_reflection","life_transition"],["calm"],
  "Evening review","What went well? What will I do differently tomorrow? One line each.",
  "شام کا جائزہ","آج کیا اچھا ہوا؟ کل کیا مختلف کروں گا؟ ہر ایک ایک سطر۔",None),
 ("intention_morning","reflection","motivational",120,["confidence","discipline","creativity"],["motivated","uncertain"],
  "Morning intention","Write one word for how you want to show up today and one action that proves it.",
  "صبح کی نیت","ایک لفظ لکھیں کہ آج آپ کیسے رہنا چاہتے ہیں، اور ایک کام جو اسے ثابت کرے۔",None),
 ("faith_routine_check","reflection","religious_practice",180,["religious_routine","spiritual_reflection"],["calm","uncertain"],
  "Faith routine check-in","Following your own tradition, note one practice you want to keep today and the time you will do it.",
  "مذہبی معمول کا جائزہ","اپنی روایت کے مطابق آج کا ایک عمل اور اس کا وقت لکھیں جسے آپ قائم رکھنا چاہتے ہیں۔",
  "Fortunis8 does not interpret religious rulings; follow your own scholars and tradition."),
 ("kind_message","practical_action","practical",180,["relationships"],["calm","motivated"],
  "One kind message","Send a short, genuine message of appreciation to someone.",
  "ایک محبت بھرا پیغام","کسی کو مختصر، سچا قدردانی کا پیغام بھیجیں۔",None),
 ("listen_fully","reflection","mindfulness",300,["relationships"],["calm"],
  "Listen fully","In your next conversation, listen without planning your reply. Afterwards note one thing you learned.",
  "پوری توجہ سے سننا","اگلی گفتگو میں جواب سوچے بغیر سنیں۔ بعد میں ایک سیکھی ہوئی بات لکھیں۔",None),
 ("idea_capture","practical_action","practical",300,["creativity","business_wealth"],["motivated","distracted"],
  "Idea capture","Write 10 rough ideas on one problem in 5 minutes. Circle one to try.",
  "خیالات کی فہرست","ایک مسئلے پر 5 منٹ میں 10 کچے خیالات لکھیں۔ ایک کو آزمانے کے لیے چنیں۔",None),
 ("make_small","practical_action","motivational",900,["creativity"],["low_energy","motivated"],
  "Make something small","Spend 15 minutes making anything: a sketch, a paragraph, a tune. Done beats perfect.",
  "کچھ چھوٹا بنائیں","15 منٹ کچھ بھی بنائیں: خاکہ، پیراگراف، دھن۔ مکمل، کامل سے بہتر ہے۔",None),
 ("walk_10","movement","scientific",600,["health_energy","stress_calm","creativity"],["low_energy","stressed"],
  "10-minute walk","Take a 10-minute walk, outdoors if you can. Notice five things you see.",
  "10 منٹ کی سیر","10 منٹ چلیں، ممکن ہو تو باہر۔ پانچ چیزیں نوٹ کریں جو نظر آئیں۔",
  "Choose a pace that is comfortable for your health."),
 ("stretch_5","movement","mindfulness",300,["health_energy","sleep_recovery"],["low_energy","stressed"],
  "Gentle 5-minute stretch","Neck, shoulders, back and legs, slowly, with easy breathing. No pain.",
  "5 منٹ ہلکی کھنچائی","گردن، کندھے، کمر اور ٹانگیں، آہستہ، آرام سے سانس کے ساتھ۔ درد نہ ہو۔",
  "Skip any movement that hurts; ask a clinician if you have an injury."),
 ("water_habit","practical_action","practical",60,["health_energy"],["low_energy"],
  "Water anchor","Drink a glass of water now and link the next glass to a meal.",
  "پانی کی عادت","ابھی ایک گلاس پانی پئیں اور اگلا گلاس کسی کھانے سے جوڑ دیں۔",None),
 ("wind_down","practical_action","scientific",600,["sleep_recovery","stress_calm"],["stressed"],
  "Wind-down","Dim lights, put the phone away, and write tomorrow's first task so your mind can let go.",
  "سونے کی تیاری","روشنی کم کریں، فون دور رکھیں، اور کل کا پہلا کام لکھ دیں تاکہ ذہن پرسکون ہو۔",None),
 ("body_scan","breath","mindfulness",420,["sleep_recovery","stress_calm"],["stressed"],
  "Body scan","Lying down, move attention slowly from toes to head, relaxing each area.",
  "جسم کا جائزہ","لیٹ کر توجہ آہستہ پاؤں سے سر تک لے جائیں اور ہر حصے کو ڈھیلا چھوڑیں۔",None),
 ("next_step_visual","visualization","visualization",180,["career_interview","confidence","business_wealth"],["uncertain"],
  "See the next step","Close your eyes and picture yourself doing the next step: where, when, the first move. Then do the first move.",
  "اگلا قدم تصور کریں","آنکھیں بند کر کے اگلا قدم کرتے خود کو دیکھیں: کہاں، کب، پہلی حرکت۔ پھر وہ پہلی حرکت کریں۔",None),
 ("transition_anchor","reflection","mixed",300,["life_transition"],["uncertain","stressed"],
  "Steady anchor","Write what is changing, what stays the same, and one routine you will keep this week.",
  "مضبوط سہارا","لکھیں کیا بدل رہا ہے، کیا وہی ہے، اور اس ہفتے کون سا معمول قائم رکھیں گے۔",None),
 ("streak_promise","practical_action","motivational",60,["discipline"],["low_energy"],
  "Two-minute promise","Pick a habit and do just two minutes of it now. Keep the streak, not the pressure.",
  "دو منٹ کا وعدہ","ایک عادت چنیں اور ابھی صرف دو منٹ کریں۔ تسلسل اہم ہے، دباؤ نہیں۔",None),
 ("reading_reflect","reading","mixed",240,["spiritual_reflection","creativity","confidence"],["uncertain","calm"],
  "Optional reading as reflection","Draw your optional reading (tarot, horoscope or palm prompt). Ask: what does this invite me to notice today? Write one action.",
  "اختیاری ریڈنگ بطور غور","اپنی اختیاری ریڈنگ دیکھیں (ٹیرو، زائچہ یا ہتھیلی کا اشارہ)۔ پوچھیں: یہ آج مجھے کس بات پر غور کی دعوت دیتی ہے؟ ایک عمل لکھیں۔",
  "Readings are for reflection and curiosity; they do not predict outcomes."),
]

def q(s):
    return "NULL" if s is None else "'" + s.replace("'", "''") + "'"

out = ["-- Fortunis8 catalog seed (draft). Generated by scripts/build_catalog_seed.py.",
       "-- Inserts rituals with active=false and source_review_status='draft' until reviewed.",
       "BEGIN;"]
for i,(k,en,ur,d) in enumerate(GOALS):
    out.append(f"INSERT INTO goal_catalog (key, display_name, description, sort_order) VALUES ({q(k)}, {q(en)}, {q(d + ' | ' + ur)}, {i}) ON CONFLICT (key) DO UPDATE SET display_name=EXCLUDED.display_name, description=EXCLUDED.description, sort_order=EXCLUDED.sort_order;")
for i,(k,en,ur,d,opt) in enumerate(MODES):
    out.append(f"INSERT INTO guidance_mode_catalog (key, display_name, description, requires_explicit_opt_in, sort_order) VALUES ({q(k)}, {q(en)}, {q(d + ' | ' + ur)}, {str(opt).upper()}, {i}) ON CONFLICT (key) DO UPDATE SET display_name=EXCLUDED.display_name, description=EXCLUDED.description, requires_explicit_opt_in=EXCLUDED.requires_explicit_opt_in, sort_order=EXCLUDED.sort_order;")
for i,(k,en,ur) in enumerate(STATES):
    out.append(f"INSERT INTO current_state_catalog (key, display_name, description, sort_order) VALUES ({q(k)}, {q(en)}, {q(ur)}, {i}) ON CONFLICT (key) DO NOTHING;")
for i,(k,en,ur) in enumerate(TRADITIONS):
    out.append(f"INSERT INTO belief_tradition_catalog (key, display_name, description, sort_order) VALUES ({q(k)}, {q(en)}, {q(ur)}, {i}) ON CONFLICT (key) DO NOTHING;")
for (k,t,m,sec,goals,states,et,ei,ut,ui,safe) in R:
    out.append(f"INSERT INTO ritual_catalog (stable_key, ritual_type, title, description, guidance_mode_key, duration_seconds) VALUES ({q(k)}, {q(t)}, {q(et)}, {q(ei)}, {q(m)}, {sec}) ON CONFLICT (stable_key, content_version) DO NOTHING;")
    rid = f"(SELECT id FROM ritual_catalog WHERE stable_key={q(k)} AND content_version=1)"
    out.append(f"INSERT INTO ritual_localizations (ritual_id, language, title, instructions, safety_note) VALUES ({rid}, 'en', {q(et)}, {q(ei)}, {q(safe)}) ON CONFLICT DO NOTHING;")
    out.append(f"INSERT INTO ritual_localizations (ritual_id, language, title, instructions, safety_note) VALUES ({rid}, 'ur', {q(ut)}, {q(ui)}, {q(safe)}) ON CONFLICT DO NOTHING;")
    for g in goals:
        out.append(f"INSERT INTO ritual_tags (ritual_id, goal_key) VALUES ({rid}, {q(g)}) ON CONFLICT DO NOTHING;")
    for s in states:
        out.append(f"INSERT INTO ritual_tags (ritual_id, current_state_key) VALUES ({rid}, {q(s)}) ON CONFLICT DO NOTHING;")
out.append("COMMIT;")

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(base, "seeds"), exist_ok=True)
open(os.path.join(base, "seeds", "fortunis8_catalog_seed.sql"), "w").write("\n".join(out) + "\n")
json.dump({"goals":GOALS,"modes":MODES,"states":STATES,"traditions":TRADITIONS,
           "rituals":[dict(zip(["key","type","mode","seconds","goals","states","en_title","en_instructions","ur_title","ur_instructions","safety_note"],r)) for r in R]},
          open(os.path.join(base, "seeds", "fortunis8_catalog.json"), "w"), ensure_ascii=False, indent=1)
# coverage check
gk={g[0] for g in GOALS}; mk={m[0] for m in MODES}
for r in R:
    assert r[2] in mk, r[0]; assert set(r[4])<=gk, r[0]
cov={g:sum(g in r[4] for r in R) for g in gk}
print(len(R),"rituals; coverage:",cov)
