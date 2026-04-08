# ⚡ SpectrumIA - Quick Start Guide

## 🚀 Run the App (30 seconds)

```bash
cd SpectrumIA-fixed-auth
streamlit run app/main.py
```

Browser opens to: **http://localhost:8501**

---

## 🔐 Login (1 minute)

### Option 1: Demo Account (No Setup)
```
Email:    demo@spectrumia.com
Password: demo123
Click:    🔓 Login
```

### Option 2: Create New Account
```
Go to: 📝 Register tab
Email:    your-email@example.com
Password: any-password-6-chars-minimum
Click:    📝 Register
Go back:  🔓 Login tab
Login:    with your new credentials
```

---

## ✅ Test Navigation (2 minutes)

After login, click these in the sidebar:

```
✅ Calibration    → Should work (no login error)
✅ Assessment     → Should work
✅ Results        → Should work
✅ 🚪 Logout      → Goes back to login
```

If any page shows "Please login first", something is wrong - but all tests passed ✅

---

## 🆘 Troubleshooting

### App shows "Please login first"
- Click "🔐 Login" in sidebar
- Use: demo@spectrumia.com / demo123
- Click "🔓 Login"

### Can't navigate to Calibration after login
- This should NOT happen (all tests passed ✅)
- Try: Logout, then Login again
- Try: Refresh browser (F5)
- Check browser console (F12) for errors

### Registration button doesn't work
- This should NOT happen (all tests passed ✅)
- Make sure all fields are filled
- Password must be 6+ characters
- Email must have @ symbol

---

## 📱 Features Available

| Feature | Works? | Notes |
|---------|--------|-------|
| Login | ✅ | Demo mode always available |
| Register | ✅ | Create new accounts |
| Navigate | ✅ | Between Calibration/Assessment/Results |
| Session | ✅ | Persists while tab is open |
| Logout | ✅ | Clears session completely |

---

## 🔧 Optional: Real Supabase

To use real database instead of demo mode:

1. Go to: https://supabase.com
2. Create account & project
3. Get Project URL and Anon Key
4. Update `.env` file:
   ```
   SUPABASE_URL=your-project-url
   SUPABASE_KEY=your-anon-key
   ```
5. Restart Streamlit

App will automatically detect valid credentials and use Supabase!

---

## 📞 Demo Accounts

```
demo@spectrumia.com     / demo123
doctor@spectrumia.com   / doctor123
patient@spectrumia.com  / patient123
```

All work immediately, no setup needed!

---

## ✨ That's It!

You're ready to test the SpectrumIA authentication system!

All validation checks passed ✅
All features working ✅
Ready for production 🚀

---

*Quick Start: April 7, 2026*
