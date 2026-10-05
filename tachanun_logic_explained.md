# לוגיקת תחנון ותוספות תפילה — פסאודוקוד להעתקה

> הערה: זו כתיבה שלי מחדש של הכללים ההלכתיים (לא קוד מועתק מהפרויקט — הפרויקט
> הנוכחי לא מכיל חישוב כזה בכלל, רק טבלת תוצאות מוכנה מראש). הפסאודוקוד הוא
> שפה-אגנוסטי, להתאמה קלה לכל שפת תכנות.

## קלטים נדרשים לכל יום

כדי לחשב את כל הדגלים, צריך פונקציית לוח שנה עברי שנותנת:

```
hdate = { year, month, day }      // תאריך עברי (לאחר שקיעה = היום הבא)
dow = 0..6                        // יום בשבוע (0=ראשון)
isLeapYear(year) -> bool          // האם שנה מעוברת (13 חודשים)
isIsrael -> bool                  // ארץ ישראל או חו"ל (משפיע על תאריכים)
```

## שלב 1: דגלי יום בסיסיים

```
function isShabbat(dow):
    return dow == 6

function isRoshChodesh(hdate):
    return hdate.day == 1 or hdate.day == 30
    // יום 30 בחודש המלא = יום ראשון דר"ח, יום 1 בחודש הבא = יום שני דר"ח

function isCholHamoed(hdate):
    if hdate.month == NISAN:  return hdate.day in [16..20]        // פסח
    if hdate.month == TISHREI: return hdate.day in [17..20]       // סוכות
    return false

function isYomTov(hdate, isIsrael):
    // רשימת תאריכי יו"ט - בחו"ל יום נוסף על כל רגל (חוץ מיוה"כ)
    table = [
        (TISHREI, 1, "ראש השנה"), (TISHREI, 2, "ראש השנה ב'"),
        (TISHREI, 10, "יום כיפור"),
        (TISHREI, 15, "סוכות"), (TISHREI, 21, "הושענא רבה/שמ"ע"),
        (TISHREI, 22, "שמחת תורה"),
        (NISAN, 15, "פסח א'"), (NISAN, 21, "פסח ז'"),
        (SIVAN, 6, "שבועות"),
    ]
    if not isIsrael: add day-after copy of כל שורה חוץ מיוה"כ
    return hdate matches any row
```

## שלב 2: דגלי "תקופה" (חודש/טווח ימים)

```
function isNissanMonth(hdate):
    return hdate.month == NISAN   // כל החודש - אין תחנון בכלל

function isSivanTachanunFree(hdate):
    // מר"ח סיון עד אסרו חג שבועות (יום אחרי שבועות)
    return hdate.month == SIVAN and hdate.day <= (isIsrael ? 7 : 8)

function isTishreiTachanunFree(hdate):
    // מערב ר"ה (29 אלול) עד אסרו חג סוכות
    return (hdate.month == ELUL and hdate.day == 29)
        or hdate.month == TISHREI and hdate.day <= (isIsrael ? 23 : 24)

function isOmerDay(hdate) -> int | null:
    // עומר: מ-16 ניסן עד 5 סיון (49 ימים)
    dayNum = daysBetween(NISAN,16, hdate)
    if 1 <= dayNum <= 49: return dayNum
    return null

function isLagBaomer(hdate):
    return isOmerDay(hdate) == 33
```

## שלב 3: תחנון — הרכבה סופית

```
function tachanunExcluded(hdate, dow, context):
    // context כולל: isMourner, isGroomWeek, isBritToday וכו' - תלוי אפליקציה
    if isShabbat(dow): return true
    if isRoshChodesh(hdate): return true
    if isYomTov(hdate) or isCholHamoed(hdate): return true
    if isNissanMonth(hdate): return true
    if isLagBaomer(hdate): return true
    if isSivanTachanunFree(hdate): return true
    if isTishreiTachanunFree(hdate): return true
    if hdate.month==AV and hdate.day==15: return true          // ט"ו באב
    if hdate.month==SHVAT and hdate.day==15: return true        // ט"ו בשבט
    if hdate.month==ADAR and hdate.day in [14,15]: return true  // פורים/שושן פורים
    if hdate.month==KISLEV_TEVET_CHANUKA_RANGE: return true     // חנוכה (8 ימים מ-25 כסלו)
    if hdate.month==NISAN... : // כבר כוסה למעלה
    if context.isErevYomTov: return true       // מנחה בלבד
    if context.isErevYomKippur: return true
    if context.isMourner: return true          // רק במניין של האבל
    if context.isGroomWeek: return true        // 7 ימי שבע ברכות
    if context.isBritTodayHere: return true    // רק במניין שבו הברית
    // (אופציונלי, תלוי מנהג): יום העצמאות, יום ירושלים
    return false
```

## שלב 4: תוספות עונתיות בעמידה

```
function mashivHaruach(hdate, isIsrael):
    // ממוסף שמ"ע (22 תשרי) עד מוסף א' פסח (15 ניסן)
    start = (TISHREI, 22)
    end   = (NISAN, 15)
    return isBetween(hdate, start, end)   // "עונתי" - לא כולל את עצם המוסף הראשון/אחרון בחצי

function talUmatar(hdate, isIsrael):
    start = isIsrael ? (CHESHVAN, 7) : gregorianDec4or5(hdate.year)
    end   = (NISAN, 15)
    return isBetween(hdate, start, end)

function yaaleVeyavo(hdate):
    return isRoshChodesh(hdate) or isCholHamoed(hdate) or isYomTov(hdate)
        // (ולא ביוה"כ - אין בו יעלה ויבוא, יש לו נוסח משלו)

function alHanisim(hdate):
    return isChanuka(hdate) or isPurim(hdate)

function aneinu(hdate, context):
    return context.isPublicFastToday and not isYomKippur(hdate)
```

## שלב 5: חיבור לפלט (כמו המנוע ב-SIDDUR, אך גנרי)

```
function renderPrayer(templateName, flags):
    text = templates[templateName]
    for each line in text:
        if line starts with "IF ":
            condName, body = parseConditionalLine(line)
            if flags[condName] == true:
                output += body
        else:
            output += line
    return output
```

זו בדיוק התבנית שראית ב-`index.html` (`()שם_תבנית תנאי`) — רק שכאן `flags` מחושב
חי מתוך תאריך, ולא נטען מראש מקובץ JSON.

## מה עוד תצטרך

- ספריית המרה ללוח עברי (gregorian↔hebrew) - זה הכי מורכב לכתוב מאפס;
  מומלץ להשתמש בספרייה קיימת כמו HebCal/KosherJava/Zmanim.js ולא לממש בעצמך.
- רשימת תעניות ציבור (NOTAANIT/TAANIT) - י' טבת, תענית אסתר, י"ז תמוז, ט' באב,
  צום גדליה.
- אם אתה צריך גם זמני היום (נץ/שקיעה) לקביעת "אור ל-" (יום לפי הלילה הקודם) -
  זה חישוב אסטרונומי נפרד (זריחה/שקיעה לפי קו רוחב/אורך), לא קשור ללוח העברי.
