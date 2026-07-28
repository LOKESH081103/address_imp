"""

Layers 1 & 3 - structural rules + placeholder/gibberish dictionary.
 
Pulled out of app.py into its own module so the exact same rule logic can be

reused outside Streamlit - e.g. by dashboard_report.py to build a standalone

presentation dashboard from the command line, or by tests, notebooks, or a

future batch/cron job. app.py imports everything it needs from here; there

is no second copy of this logic anywhere in the project.
 
Layer 2 (pincode API) and Layer 4 (ML) live in pincode_lookup.py and

ml_classifier.py respectively, for the same reason.

"""
 
import re
 
# ----------------------------------------------------------------------

# Reference data

# ----------------------------------------------------------------------

INDIAN_STATES = [

    "ANDHRA PRADESH", "ARUNACHAL PRADESH", "ASSAM", "BIHAR", "CHHATTISGARH",

    "GOA", "GUJARAT", "HARYANA", "HIMACHAL PRADESH", "JHARKHAND", "KARNATAKA",

    "KERALA", "MADHYA PRADESH", "MAHARASHTRA", "MANIPUR", "MEGHALAYA",

    "MIZORAM", "NAGALAND", "ODISHA", "PUNJAB", "RAJASTHAN", "SIKKIM",

    "TAMIL NADU", "TELANGANA", "TRIPURA", "UTTAR PRADESH", "UTTARAKHAND",

    "WEST BENGAL", "DELHI", "JAMMU AND KASHMIR", "LADAKH", "PUDUCHERRY",

    "CHANDIGARH", "ANDAMAN AND NICOBAR", "DADRA AND NAGAR HAVELI",

    "DAMAN AND DIU", "LAKSHADWEEP",

]
 
COMMON_SAFE_LONG_WORDS = {"MAHARASHTRA", "TELANGANA", "CHHATTISGARH", "PONDICHERRY", "VISAKHAPATNAM"}
 
# Recognized city/town/district names.

INDIAN_CITY_HINTS = {

    "MUMBAI", "DELHI", "NEW DELHI", "BANGALORE", "BENGALURU", "HYDERABAD", "CHENNAI",

    "KOLKATA", "PUNE", "AHMEDABAD", "SURAT", "JAIPUR", "LUCKNOW", "KANPUR", "NAGPUR",

    "INDORE", "THANE", "BHOPAL", "VISAKHAPATNAM", "VIZAG", "PATNA", "VADODARA",

    "GHAZIABAD", "LUDHIANA", "AGRA", "NASHIK", "FARIDABAD", "MEERUT", "RAJKOT",

    "VARANASI", "SRINAGAR", "AMRITSAR", "NAVI MUMBAI", "PRAYAGRAJ", "ALLAHABAD",

    "RANCHI", "HOWRAH", "COIMBATORE", "JABALPUR", "GWALIOR", "VIJAYAWADA", "JODHPUR",

    "MADURAI", "RAIPUR", "KOTA", "GUWAHATI", "CHANDIGARH", "SOLAPUR", "HUBLI",

    "MYSORE", "MYSURU", "TIRUCHIRAPPALLI", "TRICHY", "BAREILLY", "ALIGARH",

    "MORADABAD", "SALEM", "THIRUVANANTHAPURAM", "THIRUVARUR", "TIRUVARUR", "TRIVANDRUM", "BHIWANDI",

    "SAHARANPUR", "GORAKHPUR", "GUNTUR", "BIKANER", "AMRAVATI", "NOIDA", "GREATER NOIDA",

    "JAMSHEDPUR", "BHILAI", "WARANGAL", "CUTTACK", "KOCHI", "COCHIN", "NELLORE",

    "BHAVNAGAR", "DEHRADUN", "DURGAPUR", "ASANSOL", "ROURKELA", "NANDED", "KOLHAPUR",

    "AJMER", "AKOLA", "GULBARGA", "JAMNAGAR", "UJJAIN", "SILIGURI", "JHANSI", "JAMMU",

    "MANGALORE", "MANGALURU", "ERODE", "BELGAUM", "TIRUNELVELI", "MALEGAON", "GAYA",

    "JALANDHAR", "BHUBANESWAR", "TIRUPUR", "DAVANAGERE", "KOZHIKODE", "CALICUT",

    "KURNOOL", "BOKARO", "RAJAHMUNDRY", "BELLARY", "PATIALA", "AGARTALA", "BHAGALPUR",

    "MUZAFFARNAGAR", "LATUR", "DHULE", "TIRUPATI", "ROHTAK", "KORBA", "BHILWARA",

    "BRAHMAPUR", "MUZAFFARPUR", "AHMEDNAGAR", "MATHURA", "KOLLAM", "AVADI", "KADAPA",

    "SAMBALPUR", "BILASPUR", "SATARA", "BIJAPUR", "RAMPUR", "SHIVAMOGGA", "CHANDRAPUR",

    "JUNAGADH", "THRISSUR", "ALWAR", "BARDHAMAN", "KAKINADA", "NIZAMABAD", "PARBHANI",

    "TUMKUR", "KHAMMAM", "PANIPAT", "DARBHANGA", "KARNAL", "BATHINDA", "JALNA",

    "ELURU", "BARABANKI", "PURNIA", "SATNA", "MAU", "SONIPAT", "FARRUKHABAD", "SAGAR",

    "DURG", "IMPHAL", "RATLAM", "HAPUR", "ARRAH", "KARIMNAGAR", "ANANTAPUR", "ETAWAH",

    "AMBERNATH", "BHARATPUR", "BEGUSARAI", "GANDHINAGAR", "PUDUCHERRY", "PONDICHERRY",

    "SIKAR", "THOOTHUKUDI", "TUTICORIN", "REWA", "MIRZAPUR", "RAICHUR", "PALI",

    "HARIDWAR", "KATIHAR", "NAGERCOIL", "THANJAVUR", "BULANDSHAHR", "KATNI",

    "SAMBHAL", "SINGRAULI", "NADIAD", "SECUNDERABAD", "YAMUNANAGAR", "PANCHKULA",

    "BURHANPUR", "KHARAGPUR", "DINDIGUL", "GANDHIDHAM", "HOSPET", "AMBALA", "MEHSANA",

    "JORHAT", "MANSA", "SILCHAR", "TEZPUR", "SHIMLA", "MANALI", "GANGTOK", "AIZAWL",

    "KOHIMA", "ITANAGAR", "DISPUR", "PANAJI", "PANJIM", "DAMAN", "DIU", "SILVASSA",

    "LEH", "KARGIL", "PORT BLAIR", "KAVARATTI", "MOGAPPAIR", "ABOHAR", "ADILABAD", 

    "MOTIHARI", "BETTIAH", "EAST CHAMPARAN", "WEST CHAMPARAN", "CHAMPARAN",

    "AJITGARH", "ALIPORE", "ALAPPUZHA", "ALLEPPEY", "AMARAVATI", "AMAMBIKAPUR", 

    "AMRELI", "AMROHA", "ANAND", "ANANTNAG", "AURANGABAD", "AZAMGARH", "BADLAPUR", 

    "BAGALKOT", "BAHADURGARH", "BAHARAMPUR", "BAHRAICH", "BALASORE", "BALESHWAR", 

    "BALLARI", "BALLIA", "BALLY", "BALURGHAT", "BANDA", "BANDIPORE", "BANKURA", 

    "BANSWARA", "BARAMULLA", "BARAN", "BARGARH", "BARIPADA", "BARMER", "BARNALA", 

    "BARODA", "BASIRHAT", "BASTI", "BATALA", "BEAWAR", "BEED", "BELAGAVI", 

    "BERHAMPUR", "BETTIAH", "BETUL", "BHADRAK", "BHANDARA", "BHARUCH", "BHIMAVARAM", 

    "BHIND", "BHIWANI", "BHUJ", "BIDAR", "BIDHANNAGAR", "BIHAR SHARIF", "BONGAIGAON", 

    "BOTAD", "BUDAUN", "BULDHANA", "BURDWAN", "BUXAR", "CALCUTTA", "CANNANORE", 

    "CHAIABASA", "CHAMBA", "CHAPRA", "CHHATARPUR", "CHHATRAPATI SAMBHAJINAGAR", 

    "CHHINDWARA", "CHIKKAMAGALURU", "CHIKMAGALUR", "CHIPLUN", "CHITRADURGA", 

    "CHITTOOR", "CHURU", "CUDDAPAH", "DAHOD", "DALTONGANJ", "DAMOH", "DANAPUR", 

    "DARJEELING", "DATIA", "DEHRI", "DEOGHAR", "DEWAS", "DHANBAD", "DHAR", 

    "DHARAMSHALA", "DHARASHIV", "DHARWAD", "DHOLPUR", "DIBRUGARH", "DIMA HASAO", 

    "DIMAPUR", "ENGLISH BAZAR", "ERNAKULAM", "ETAH", "FAIZABAD", "FARIDKOT", 

    "FATEHABAD", "FATEHPUR", "FIROZABAD", "FIROZPUR", "GADAG", "GANGANAGAR", 

    "GAUHATI", "GHAZIPUR", "GIRIDIH", "GODHRA", "GONDA", "GONDIA", "GUNA", 

    "GURDASPUR", "GURGAON", "GURUGRAM", "HAJIPUR", "HALDIA", "HALDWANI", 

    "HANUMANGARH", "HARDOI", "HASSAN", "HATHRAS", "HAZARIBAGH", "HINDUPUR", 

    "HISAR", "HOSHIARPUR", "HOSAPETE", "HOSUR", "HUBBALLI", "HUGLI", "ISLAMPUR", 

    "JAGDALPUR", "JAGGAIAHPETA", "JAGTIAL", "JAISALMER", "JALAUN", "JALGAON", 

    "JALPAIGURI", "JAMALPUR", "JAUNPUR", "JEHANABAD", "JHARSUGUDA", "JHUNJHUNU", 

    "JIND", "KAITHAL", "KALABURAGI", "KALYAN", "KAMAREDDY", "KANCHEEPURAM", 

    "KANCHIPURAM", "KANNUR", "KAPURTHALA", "KARAIKUDI", "KARUR", "KASARAGOD", 

    "KASHIPUR", "KENDUJHAR", "KHAMGAON", "KHANDWA", "KHARGONE", "KISHANGARH", 

    "KOLAR", "KOPPAL", "KOTAKAPURA", "KOTTAYAM", "KRISHNANAGAR", "KULLU", 

    "KUMBAKONAM", "KURUKSHETRA", "MACHILIPATNAM", "MADANAPALLE", "MADRAS", 

    "MAHBUBNAGAR", "MAHESANA", "MAHOBA", "MALERKOTLA", "MANDI", "MANDSAUR", 

    "MANDYA", "MANGALAGIRI", "MANGO", "MANIPAL", "MARGAO", "MAYILADUTHURAI", 

    "MEDININAGAR", "MIDNAPORE", "MIRA-BHAYANDAR", "MODINAGAR", "MOGA", "MOHALI", 

    "MORBI", "MORENA", "MOTIHARI", "MUKTSAR", "MUNGER", "MURSHIDABAD", "MURWARA", 

    "MUSSOORIE", "NABADWIP", "NAGAON", "NAGAUR", "NAINITAL", "NALGONDA", 

    "NAMAKKAL", "NANDURBAR", "NANDYAL", "NARASARAOPET", "NAVSARI", "NEEMUCH", 

    "ONGOLE", "OOTY", "ORAI", "OSMANABAD", "PALAKKAD", "PALANPUR", "PALGHAR", 

    "PALGHAT", "PALWAL", "PANDHARPUR", "PANVEL", "PATHANKOT", "PHAGWARA", 

    "PHUSRO", "PIMPRI-CHINCHWAD", "PORBANDAR", "PUDUKKOTTAI", "PURI", "PURULIA", 

    "QUILON", "RAEBARELI", "RAIGARH", "RAIGANJ", "RAJAMAHENDRAVARAM", "RAJPURA", 

    "RAJNANDGAON", "RAMAGUNDAM", "RAMANATHAPURAM", "RAMGARH", "RATNAGIRI", 

    "REWARI", "RISHIKESH", "ROORKEE", "RUDRAPUR", "SAHARSA", "SALT LAKE", 

    "SANGLI", "SANTIPUR", "SASARAM", "SAWAI MADHOPUR", "SEHORE", "SHAHDOL", 

    "SHAHJAHANPUR", "SHILLONG", "SHIMOGA", "SHIVPURI", "SIRMAUR", "SIROHI", 

    "SIRSA", "SITAPUR", "SIWAN", "SOLAN", "SRI GANGANAGAR", "SRIKAKULAM", 

    "SURENDRANAGAR", "SURYAPET", "TADEPALLIGUDEM", "TADIPATRI", "TAMBARAM", 

    "TENALI", "THANESAR", "TINSUKIA", "TIRUPPUR", "TIRUVANNAMALAI", "TONK", 

    "TRICHUR", "TUMAKURU", "UDAIPUR", "UDHAGAMANDALAM", "UDUPI", "ULHASNAGAR", 

    "UNNAO", "VALSAD", "VAPI", "VASAI", "VASCO", "VELLORE", "VIDISHA", 

    "VIJAYAPURA", "VILLUPURAM", "VIRAR", "VIZIANAGARAM", "WARDHA", "YAVATMAL",

}
 
INDIAN_CITY_HINTS = {c.upper() for c in INDIAN_CITY_HINTS}
 
PLACEHOLDER_PHRASES = {

    "NA", "N A", "N/A", "N.A", "N.A.", "NIL", "NONE", "XXX", "XXXX", "XYZ", "ABC",

    "TEST", "TESTING", "TBD", "PENDING", "DUMMY", "SAMPLE", "DEFAULT", "UNKNOWN",

    "NOT AVAILABLE", "ADDRESS NOT AVAILABLE", "SAME AS ABOVE", "SAME AS PREVIOUS",

    "ASDF", "ASDFGH", "QWERTY",

}

PLACEHOLDER_WORDS = {"TEST", "TESTING", "TBD", "DUMMY", "SAMPLE", "ASDF", "ASDFGH", "QWERTY", "XYZ", "NIL", "NULL"}
 
FOREIGN_LOCATION_HINTS = {

    "DUBAI", "UAE", "ABU DHABI", "SHARJAH", "SINGAPORE", "LONDON", "USA",

    "UNITED STATES", "UNITED KINGDOM", "CANADA", "AUSTRALIA", "NEPAL", "DOHA", "QATAR",

}
 
CRITICAL_ISSUE_PREFIXES = {

    "EMPTY_ADDRESS", "MISSING_PINCODE", "PINCODE_NOT_FOUND_IN_INDIA",

    "PLACEHOLDER_ADDRESS", "ADDRESS_TOO_SHORT",

    "HOUSE_NO_ZERO_OR_PLACEHOLDER", "MISSING_HOUSE_OR_PLOT_NUMBER",

}
 
ISSUE_DESCRIPTIONS = {

    "EMPTY_ADDRESS": "Address field is blank",

    "DOUBLE_COMMA_EMPTY_FIELD": "Contains ',,' - an empty field between commas",

    "PINCODE_DUPLICATED": "6-digit pincode appears twice back-to-back",

    "PINCODE_GLUED_TO_TEXT": "Pincode is stuck directly to a word with no space",

    "MISSING_PINCODE": "No 6-digit pincode found",

    "STATE_NOT_FOUND": "No recognizable Indian state name in the address",

    "ADDRESS_TOO_SHORT": "Address has very few words - likely incomplete",

    "POSSIBLE_MERGED_WORDS": "A long word may be two+ words stuck together",

    "HOUSE_NO_ZERO_OR_PLACEHOLDER": "House/flat number looks like a placeholder",

    "MISSING_HOUSE_OR_PLOT_NUMBER": "No house/door/flat/plot number found - only locality-level detail, nothing that pinpoints the exact building",

    "PINCODE_NOT_FOUND_IN_INDIA": "Pincode doesn't exist in the official India Post database",

    "PINCODE_STATE_MISMATCH": "Pincode belongs to a different state than what's written",

    "PLACEHOLDER_ADDRESS": "Entire address is a placeholder value (NA, TEST, etc.)",

    "PLACEHOLDER_WORD": "Contains a placeholder/junk word",

    "FOREIGN_LOCATION_MENTIONED": "Mentions a location outside India",

    "REPEATED_CHARACTER_RUN": "Same character repeated 4+ times in a row (e.g. aaaa)",

    "POSSIBLE_GIBBERISH_TEXT": "Long run of consonants suggests random/gibberish text",

    "ML_FLAGGED_PATTERN": "ML classifier judged this address's text patterns as issue-like",

}
 
DEMO_DATA = [

    ("AGR001", "ABHISHEK BUNGALOW NO. ONEKALPATARU NAGAR ASHOKA MARG , 422011"),

    ("AGR002", "SECTOR NO-4,CBD BELAPUR , NAVI MUMBAI400206"),

    ("AGR003", "FLAT NO- X, 5 TH FLOOR, BEACON CHSSOUTH AVENUEOPP RAMKRISHNA MISSION HOSPITAL, , SANTACRUZ-W, MUMBAI- 400054400054"),

    ("AGR004", "# 0, INSIDE NEW MARKET BAGGA MARKET , ,JAGADHRI YAMUNA NAGAR HARYANA - 135001"),

    ("AGR005", "# INDUSTRIEL AREA, , NEAR JODI FNAST ROAD YAMUNA NAGAR HARYANA - 135002"),

    ("AGR006", "# CHHACHHROULI ROAD, JAGADHRI, , YAMUNA NAGAR HARYANA - 135002"),

    ("AGR007", "YELAMANCHILI ROADATCHUT,APURAM, MAIN ROAD , ,MAIN ROAD531011"),

    ("AGR008", "12, GREEN PARK EXTENSION, NEW DELHI, DELHI - 110016"),

    ("AGR009", "MAIN ROAD 1, DUBAI"),

    ("AGR010", "NA"),

    ("AGR011", "FLAT 302 SUNRISE APARTMENTS MG ROAD BANGALORE KARNATAKA - 999999"),

]
 
 
def describe_issue(issue: str) -> str:

    base = issue.split("(")[0]

    return ISSUE_DESCRIPTIONS.get(base, base)
 
 
def severity_for(issue_codes, ml_prob=None):

    """

    Only two outcomes: "Critical" or "Clean".
 
      - No issues -> Clean.

      - Any critical issue present (empty address, missing pincode, placeholder,

        or MISSING_HOUSE_OR_PLOT_NUMBER / HOUSE_NO_ZERO_OR_PLACEHOLDER) -> Always Critical.

      - If NO critical issue is present (i.e., a valid door/house/ward/building number exists)

        AND total issue count is 1 or 2 (e.g., only ML_FLAGGED_PATTERN or minor notice) -> Clean.

      - Otherwise (issue_codes count > 2 with non-critical issues):

        Clean if ml_prob < 0.5, else Critical.

    """

    if not issue_codes:

        return "Clean"
 
    has_critical_issue = any(i.split("(")[0] in CRITICAL_ISSUE_PREFIXES for i in issue_codes)
 
    # 1. If there is NO door number (or any other critical flaw), always mark Critical.

    if has_critical_issue:

        return "Critical"
 
    # 2. If door number exists and issue count is 1 or 2 (e.g., ML_FLAGGED_PATTERN alone), mark Clean.

    if len(issue_codes) <= 2:

        return "Clean"
 
    # 3. Fallback for >2 non-critical issues

    if ml_prob is None:

        return "Critical"

    return "Clean" if ml_prob < 0.5 else "Critical"
 
 
# ----------------------------------------------------------------------

# Layer 1 - structural rules

# ----------------------------------------------------------------------

def layer1_structural(addr: str, tokens, pins, min_words: int = 5, merge_len_threshold: int = 15):

    issues = []

    if re.search(r",\s*,", addr):

        issues.append("DOUBLE_COMMA_EMPTY_FIELD")

    if re.search(r"(\d{6})\1", addr):

        issues.append("PINCODE_DUPLICATED")

    glued_match = re.search(r"[A-Za-z](\d{6})\b", addr)

    if glued_match and "PINCODE_DUPLICATED" not in issues:

        issues.append("PINCODE_GLUED_TO_TEXT")
 
    state_found = any(state in addr.upper() for state in INDIAN_STATES)

    city_found = any(city in addr.upper() for city in INDIAN_CITY_HINTS)

    if not state_found and not city_found:

        issues.append("STATE_NOT_FOUND")
 
    phrase_counts = {}

    for n in (2, 3):

        for i in range(len(tokens) - n + 1):

            phrase = " ".join(tokens[i:i + n])

            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

    repeated = [p for p, c in phrase_counts.items() if c > 1 and len(p) > 6]

    if repeated:

        issues.append(f"REPEATED_PHRASE({repeated[0]})")
 
    long_tokens = [t for t in tokens if len(t) >= merge_len_threshold and t not in COMMON_SAFE_LONG_WORDS]
 
    if len(tokens) < min_words and not long_tokens:

        issues.append("ADDRESS_TOO_SHORT")
 
    if long_tokens:

        issues.append(f"POSSIBLE_MERGED_WORDS({long_tokens[0]})")
 
    if re.search(r"#\s*0\b", addr) or re.search(

        r"(?:H\.?\s*NO|HOUSE\s*NO|FLAT\s*NO|DOOR\s*NO|PLOT\s*NO)\.?\s*[-:]?\s*0\b", addr, re.IGNORECASE

    ):

        issues.append("HOUSE_NO_ZERO_OR_PLACEHOLDER")

    elif not _has_specific_location_number(addr, pins):

        issues.append("MISSING_HOUSE_OR_PLOT_NUMBER")
 
    return issues
 
 
def _has_specific_location_number(addr: str, pins) -> bool:

    """

    True if the address contains any digit that ISN'T part of a recognized

    pincode - e.g., house/door/flat/plot/ward/building number like "353", "Ward-02", "45", etc.

    """

    cleaned = addr

    for p in pins:

        if len(p) == 6:

            for variant in (p, f"{p[:3]} {p[3:]}", f"{p[:3]}-{p[3:]}"):

                cleaned = cleaned.replace(variant, " ")

    return bool(re.search(r"\d", cleaned))
 
 
# ----------------------------------------------------------------------

# Layer 2 helpers - pincode extraction

# ----------------------------------------------------------------------

_PIN_PATTERN = re.compile(r"\b(\d{3})[ -](\d{3})\b|\b(\d{6})\b")

_DUPLICATED_PIN = re.compile(r"(\d{6})\1")

_LONG_DIGIT_RUN = re.compile(r"\d{7,}")

_LABELED_NUMBER_BEFORE_PIN = re.compile(

    r"(?:H\.?\s*NO|HOUSE\s*NO|FLAT\s*NO|DOOR\s*NO|PLOT\s*NO|QUARTER\s*NO|KHATA\s*NO|ROOM\s*NO)"

    r"\.?\s*[-:]?\s*(\d{6})\b",

    re.IGNORECASE,

)
 
 
def extract_pins(addr: str):

    pins = set()
 
    for m in _DUPLICATED_PIN.finditer(addr):

        pins.add(m.group(1))
 
    for m in _PIN_PATTERN.finditer(addr):

        pins.add(m.group(3) if m.group(3) else m.group(1) + m.group(2))
 
    pins |= set(re.findall(r"[A-Za-z](\d{6})\b", addr))
 
    for run in _LONG_DIGIT_RUN.findall(addr):

        pins.add(run[-6:])
 
    labeled_house_numbers = set(_LABELED_NUMBER_BEFORE_PIN.findall(addr))

    if labeled_house_numbers and (pins - labeled_house_numbers):

        pins -= labeled_house_numbers
 
    return pins
 
 
def layer2_issues_from_results(addr_upper: str, pins: set, pin_results: dict):

    if not pins:

        return [], "skipped"

    issues = []

    network_status = "ok"

    for pin in sorted(pins):

        result = pin_results.get(pin, "ERROR")

        if result is None:

            issues.append("PINCODE_NOT_FOUND_IN_INDIA")

        elif result == "ERROR":

            network_status = "error"

        else:

            actual_state = str(result.get("state", "")).upper()

            if actual_state and actual_state not in addr_upper:

                other_states = [s for s in INDIAN_STATES if s in addr_upper and s != actual_state]

                if other_states:

                    issues.append(f"PINCODE_STATE_MISMATCH(pin={pin} actual={actual_state} stated={other_states[0]})")

    return issues, network_status
 
 
# ----------------------------------------------------------------------

# Layer 3 - placeholder / gibberish / foreign-location dictionary

# ----------------------------------------------------------------------

def layer3_placeholder_gibberish(addr_upper: str, tokens):

    issues = []

    stripped = re.sub(r"[^A-Z ]", " ", addr_upper)

    stripped = re.sub(r"\s+", " ", stripped).strip()

    if stripped in PLACEHOLDER_PHRASES:

        issues.append("PLACEHOLDER_ADDRESS")
 
    hit = set(tokens) & PLACEHOLDER_WORDS

    if hit and "PLACEHOLDER_ADDRESS" not in issues:

        issues.append(f"PLACEHOLDER_WORD({sorted(hit)[0]})")
 
    foreign_hit = [f for f in FOREIGN_LOCATION_HINTS if f in addr_upper]

    if foreign_hit:

        issues.append(f"FOREIGN_LOCATION_MENTIONED({foreign_hit[0]})")
 
    if re.search(r"([A-Za-z0-9])\1{3,}", addr_upper):

        issues.append("REPEATED_CHARACTER_RUN")
 
    if re.search(r"[BCDFGHJKLMNPQRSTVWXYZ]{6,}", addr_upper):

        issues.append("POSSIBLE_GIBBERISH_TEXT")
 
    return issues
 
 
# ----------------------------------------------------------------------

# Orchestration

# ----------------------------------------------------------------------

def analyze_address_local(addr, min_words: int = 5, merge_len_threshold: int = 15):

    if not isinstance(addr, str) or not addr.strip():

        return ["EMPTY_ADDRESS"], "", set()
 
    addr = addr.strip()

    addr_upper = addr.upper()

    tokens = re.findall(r"[A-Za-z]+", addr_upper)

    pins = extract_pins(addr)
 
    issues = []

    issues += layer1_structural(addr, tokens, pins, min_words, merge_len_threshold)

    issues += layer3_placeholder_gibberish(addr_upper, tokens)
 
    if not pins and "MISSING_PINCODE" not in issues:

        issues.append("MISSING_PINCODE")
 
    return issues, addr_upper, pins
 
 
def dedupe(issues):

    seen = set()

    out = []

    for i in issues:

        if i not in seen:

            seen.add(i)

            out.append(i)

    return out
 