from dataclasses import dataclass, field
@dataclass
class TestCase:
    id: str
    query: str
    preferred: tuple[str, str] | None
    acceptable: list[tuple[str, str]]
    category_filter: str | None = None
    notes: str = ""

TEST_CASES: list[TestCase] = [

TestCase(
    id="BNSS_001",
    query="police arrested me without informing the reason",
    preferred=("Bharatiya Nagarik Suraksha Sanhita 2023", "47"),
    acceptable=[
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "47"),
    ],
    category_filter="criminal",
    notes="Rights of arrested person: grounds of arrest and information.",
),

TestCase(
    id="BNSS_002",
    query="can police arrest without warrant",
    preferred=("Bharatiya Nagarik Suraksha Sanhita 2023", "35"),
    acceptable=[
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "35"),
        ("Bharatiya Nagarik Suraksha Sanhita 2023","36")
    ],
    category_filter="criminal",
    notes="Arrest without warrant powers.",
),

TestCase(
    id="BNSS_003",
    query="how long can police keep me in custody",
    preferred=("Bharatiya Nagarik Suraksha Sanhita 2023", "58"),
    acceptable=[
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "58"),
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "187"),
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "57")
    ],
    category_filter="criminal",
    notes="Custody limits and production before magistrate.",
),

TestCase(
    id="BNSS_004",
    query="do I have right to legal aid during arrest",
    preferred=("Bharatiya Nagarik Suraksha Sanhita 2023", "38"),
    acceptable=[
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "38"),
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "341"),
    ],
    category_filter="criminal",
    notes="Right to legal counsel.",
),

TestCase(
    id="BNSS_005",
    query="what happens after police complete investigation",
    preferred=("Bharatiya Nagarik Suraksha Sanhita 2023", "193"),
    acceptable=[
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "193"),
    ],
    category_filter="criminal",
    notes="Investigation procedure after FIR.",
),

TestCase(
    id="BNSS_006",
    query="can police search my house without permission",
    preferred=("Bharatiya Nagarik Suraksha Sanhita 2023", "96"),
    acceptable=[
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "96"),
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "185"),
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "97")
    ],
    category_filter="criminal",
    notes="Search and seizure powers.",
),

TestCase(
    id="BNSS_009",
    query="can I get summons instead of arrest",
    preferred=("Bharatiya Nagarik Suraksha Sanhita 2023", "35"),
    acceptable=[
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "35"),
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "90"),
    ],
    category_filter="criminal",
    notes="Summons vs warrant system.",
),

TestCase(
    id="BNSS_010",
    query="what is charge sheet and when is it filed",
    preferred=("Bharatiya Nagarik Suraksha Sanhita 2023", "193"),
    acceptable=[
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "193"),
    ],
    category_filter="criminal",
    notes="Police report / charge sheet filing.",
),

TestCase(
    id="BNSS_011",
    query="can police remand me repeatedly",
    preferred=("Bharatiya Nagarik Suraksha Sanhita 2023", "187"),
    acceptable=[
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "187"),
    ],
    category_filter="criminal",
    notes="Remand and custody extension rules.",
),

TestCase(
    id="BNSS_012",
    query="what rights do I have during police interrogation",
    preferred=("Bharatiya Nagarik Suraksha Sanhita 2023", "180"),
    acceptable=[
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "180"),
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "181"),
        ("Bharatiya Nagarik Suraksha Sanhita 2023", "183"),
    ],
    category_filter="criminal",
    notes="Statements to police and protection against coercion.",
),

TestCase(
    id="BNS_001",
    query="someone stole my phone what legal action can I take",
    preferred=("Bharatiya Nyaya Sanhita 2023", "303"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "303"),
        ("Bharatiya Nyaya Sanhita 2023", "305"),
    ],
    category_filter="criminal",
    notes="Theft and aggravated theft cluster.",
),

TestCase(
    id="BNS_002",
    query="what is punishment for robbery or armed robbery",
    preferred=("Bharatiya Nyaya Sanhita 2023", "309"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "309"),
        ("Bharatiya Nyaya Sanhita 2023", "310"),
    ],
    category_filter="criminal",
    notes="Robbery and dacoity cluster.",
),

TestCase(
    id="BNS_003",
    query="someone hit me and caused injury",
    preferred=("Bharatiya Nyaya Sanhita 2023", "115"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "115"),
        ("Bharatiya Nyaya Sanhita 2023", "117"),
        ("Bharatiya Nyaya Sanhita 2023", "116"),
    ],
    category_filter="criminal",
    notes="Hurt and grievous hurt.",
),

TestCase(
    id="BNS_004",
    query="murder punishment in india",
    preferred=("Bharatiya Nyaya Sanhita 2023", "101"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "101"),
        ("Bharatiya Nyaya Sanhita 2023", "103"),
    ],
    category_filter="criminal",
    notes="Homicide and murder.",
),

TestCase(
    id="BNS_005",
    query="attempt to murder case punishment",
    preferred=("Bharatiya Nyaya Sanhita 2023", "110"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "110"),
    ],
    category_filter="criminal",
),

TestCase(
    id="BNS_006",
    query="rape or sexual assault punishment",
    preferred=("Bharatiya Nyaya Sanhita 2023", "63"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "63"),
        ("Bharatiya Nyaya Sanhita 2023", "64"),
    ],
    category_filter="criminal",
    notes="Sexual offences cluster.",
),

TestCase(
    id="BNS_007",
    query="harassment or stalking a woman online or offline",
    preferred=("Bharatiya Nyaya Sanhita 2023", "75"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "75"),
        ("Bharatiya Nyaya Sanhita 2023", "78"),
    ],
    category_filter="criminal",
),

TestCase(
    id="BNS_008",
    query="cheating or online fraud scam case",
    preferred=("Bharatiya Nyaya Sanhita 2023", "318"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "318"),
        ("Bharatiya Nyaya Sanhita 2023", "319"),
    ],
    category_filter="criminal",
    notes="Cheating and fraud.",
),

TestCase(
    id="BNS_009",
    query="criminal breach of trust or misuse of money",
    preferred=("Bharatiya Nyaya Sanhita 2023", "316"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "316"),
    ],
    category_filter="criminal",
),

TestCase(
    id="BNS_010",
    query="defamation case for false allegations",
    preferred=("Bharatiya Nyaya Sanhita 2023", "356"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "356"),
    ],
    category_filter="criminal",
),

TestCase(
    id="BNS_011",
    query="kidnapping or abduction of a person",
    preferred=("Bharatiya Nyaya Sanhita 2023", "137"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "137"),
        ("Bharatiya Nyaya Sanhita 2023", "138"),
    ],
    category_filter="criminal",
),

TestCase(
    id="BNS_012",
    query="criminal intimidation or threats",
    preferred=("Bharatiya Nyaya Sanhita 2023", "351"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "351"),
    ],
    category_filter="criminal",
),

TestCase(
    id="BNS_013",
    query="public fight disturbing peace or rioting",
    preferred=("Bharatiya Nyaya Sanhita 2023", "191"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "191"),
        ("Bharatiya Nyaya Sanhita 2023", "189"),
    ],
    category_filter="criminal",
),

TestCase(
    id="BNS_014",
    query="forgery of documents or fake certificate",
    preferred=("Bharatiya Nyaya Sanhita 2023", "336"),
    acceptable=[
        ("Bharatiya Nyaya Sanhita 2023", "336"),
        ("Bharatiya Nyaya Sanhita 2023", "337"),
    ],
    category_filter="criminal",
),

TestCase(
    id="IDA_001",
    query="can employer fire me without any notice in India",
    preferred=("Industrial Disputes Act 1947", "25F"),
    acceptable=[("Industrial Disputes Act 1947", "25F"), ("Industrial Disputes Act 1947", "25N")],
    category_filter="labour",
),

TestCase(
    id="IDA_002",
    query="what is retrenchment compensation",
    preferred=("Industrial Disputes Act 1947", "25F"),
    acceptable=[("Industrial Disputes Act 1947", "25F"), ("Industrial Disputes Act 1947", "25N")],
    category_filter="labour",
),

TestCase(
    id="IDA_003",
    query="how can I file industrial dispute against company",
    preferred=("Industrial Disputes Act 1947", "10"),
    acceptable=[("Industrial Disputes Act 1947", "10")],
    category_filter="labour",
),

TestCase(
    id="IDA_004",
    query="what is illegal strike or lockout",
    preferred=("Industrial Disputes Act 1947", "22"),
    acceptable=[("Industrial Disputes Act 1947", "22"), ("Industrial Disputes Act 1947", "23")],
    category_filter="labour",
),

TestCase(
    id="IDA_005",
    query="when is termination considered illegal",
    preferred=("Industrial Disputes Act 1947", "25N"),
    acceptable=[("Industrial Disputes Act 1947", "25N"), ("Industrial Disputes Act 1947", "25F")],
    category_filter="labour",
),

TestCase(
    id="IDA_006",
    query="can company close factory without government approval",
    preferred=("Industrial Disputes Act 1947", "25O"),
    acceptable=[("Industrial Disputes Act 1947", "25O"), ("Industrial Disputes Act 1947", "25M")],
    category_filter="labour",
),

TestCase(
    id="OSH_001",
    query="what safety measures must factories provide for workers",
    preferred=("Occupational Safety Health And Working Conditions Code 2020", "6"),
    acceptable=[("Occupational Safety Health And Working Conditions Code 2020", "6"), ("Occupational Safety Health And Working Conditions Code 2020", "13")],
    category_filter="labour",
),

TestCase(
    id="OSH_002",
    query="can I refuse unsafe work in factory",
    preferred=("Occupational Safety Health And Working Conditions Code 2020", "15"),
    acceptable=[("Occupational Safety Health And Working Conditions Code 2020", "15")],
    category_filter="labour",
),

TestCase(
    id="OSH_003",
    query="what is maximum working hours per day in factory",
    preferred=("Occupational Safety Health And Working Conditions Code 2020", "25"),
    acceptable=[("Occupational Safety Health And Working Conditions Code 2020", "25"), ("Occupational Safety Health And Working Conditions Code 2020", "28")],
    category_filter="labour",
),

TestCase(
    id="OSH_004",
    query="what happens if employer violates safety rules",
    preferred=("Occupational Safety Health And Working Conditions Code 2020", "41"),
    acceptable=[("Occupational Safety Health And Working Conditions Code 2020", "41"), ("Occupational Safety Health And Working Conditions Code 2020", "42")],
    category_filter="labour",
),

TestCase(
    id="OSH_005",
    query="are workers entitled to health checkups at workplace",
    preferred=("Occupational Safety Health And Working Conditions Code 2020", "13"),
    acceptable=[("Occupational Safety Health And Working Conditions Code 2020", "13"), ("Occupational Safety Health And Working Conditions Code 2020", "14")],
    category_filter="labour",
),

TestCase(
    id="OSH_006",
    query="do companies need safety officer for factory",
    preferred=("Occupational Safety Health And Working Conditions Code 2020", "22"),
    acceptable=[("Occupational Safety Health And Working Conditions Code 2020", "22")],
    category_filter="labour",
),

TestCase(
    id="PWA_001",
    query="can employer delay salary payment",
    preferred=("Payment Of Wages Act 1936", "4"),
    acceptable=[("Payment Of Wages Act 1936", "4"), ("Payment Of Wages Act 1936", "5")],
    category_filter="labour",
),

TestCase(
    id="PWA_002",
    query="what is time limit for salary payment",
    preferred=("Payment Of Wages Act 1936", "5"),
    acceptable=[("Payment Of Wages Act 1936", "5")],
    category_filter="labour",
),

TestCase(
    id="PWA_003",
    query="can salary be deducted without reason",
    preferred=("Payment Of Wages Act 1936", "7"),
    acceptable=[("Payment Of Wages Act 1936", "7"), ("Payment Of Wages Act 1936", "8")],
    category_filter="labour",
),

TestCase(
    id="PWA_004",
    query="what deductions are legal from wages",
    preferred=("Payment Of Wages Act 1936", "7"),
    acceptable=[("Payment Of Wages Act 1936", "7")],
    category_filter="labour",
),

TestCase(
    id="PWA_005",
    query="what to do if employer does not pay salary",
    preferred=("Payment Of Wages Act 1936", "15"),
    acceptable=[("Payment Of Wages Act 1936", "15"), ("Payment Of Wages Act 1936", "17")],
    category_filter="labour",
),

TestCase(
    id="PWA_006",
    query="can company pay salary in cash instead of bank transfer",
    preferred=("Payment Of Wages Act 1936", "6"),
    acceptable=[("Payment Of Wages Act 1936", "6")],
    category_filter="labour",
),

TestCase(
    id="CSS_001",
    query="who is eligible for provident fund under social security code",
    preferred=("The Code On Security 2020", "142"),
    acceptable=[("The Code On Security 2020", "142"), ("The Code On Security 2020", "143")],
    category_filter="labour",
),

TestCase(
    id="CSS_002",
    query="is gratuity mandatory for all employees",
    preferred=("The Code On Security 2020", "53"),
    acceptable=[("The Code On Security 2020", "53"), ("The Code On Security 2020", "54")],
    category_filter="labour",
),

TestCase(
    id="CSS_003",
    query="what benefits are available for gig workers",
    preferred=("The Code On Security 2020", "114"),
    acceptable=[("The Code On Security 2020", "114"), ("The Code On Security 2020", "115")],
    category_filter="labour",
),

TestCase(
    id="CSS_004",
    query="how is employee insurance provided under law",
    preferred=("The Code On Security 2020", "39"),
    acceptable=[("The Code On Security 2020", "39"), ("The Code On Security 2020", "40")],
    category_filter="labour",
),

TestCase(
    id="CSS_005",
    query="can employer avoid social security contributions",
    preferred=("The Code On Security 2020", "141"),
    acceptable=[("The Code On Security 2020", "141"), ("The Code On Security 2020", "142")],
    category_filter="labour",
),

TestCase(
    id="CSS_006",
    query="what happens if company does not deposit PF contributions",
    preferred=("The Code On Security 2020", "143"),
    acceptable=[("The Code On Security 2020", "143"), ("The Code On Security 2020", "142")],
    category_filter="labour",
),

TestCase(
    id="ECA_001",
    query="what compensation is given if worker dies in workplace accident",
    preferred=("The Employees Compensation Act 1923", "3"),
    acceptable=[("The Employees Compensation Act 1923", "3"), ("The Employees Compensation Act 1923", "4")],
    category_filter="labour",
),

TestCase(
    id="ECA_002",
    query="who pays compensation for work injury",
    preferred=("The Employees Compensation Act 1923", "4"),
    acceptable=[("The Employees Compensation Act 1923", "4")],
    category_filter="labour",
),

TestCase(
    id="ECA_003",
    query="how is compensation calculated for disability at work",
    preferred=("The Employees Compensation Act 1923", "4"),
    acceptable=[("The Employees Compensation Act 1923", "4"), ("The Employees Compensation Act 1923", "4A")],
    category_filter="labour",
),

TestCase(
    id="ECA_004",
    query="what injuries are covered under employee compensation law",
    preferred=("The Employees Compensation Act 1923", "3"),
    acceptable=[("The Employees Compensation Act 1923", "3")],
    category_filter="labour",
),

TestCase(
    id="ECA_005",
    query="can employee claim compensation if accident happens while commuting",
    preferred=("The Employees Compensation Act 1923", "3"),
    acceptable=[("The Employees Compensation Act 1923", "3"), ("The Employees Compensation Act 1923", "4")],
    category_filter="labour",
),

TestCase(
    id="ECA_006",
    query="what is employer liability in workplace injury cases",
    preferred=("The Employees Compensation Act 1923", "4"),
    acceptable=[("The Employees Compensation Act 1923", "4")],
    category_filter="labour",
),

TestCase(
    id="JJ_001",
    query="What happens if a child commits a crime in India?",
    preferred=("Juvenile Justice Act 2015", "15"),
    acceptable=[("Juvenile Justice Act 2015", "15"), ("Juvenile Justice Act 2015", "18")],
    category_filter="women_child",
),

TestCase(
    id="JJ_002",
    query="Can a minor be tried as an adult in serious cases?",
    preferred=("Juvenile Justice Act 2015", "15"),
    acceptable=[("Juvenile Justice Act 2015", "15")],
    category_filter="women_child",
),

TestCase(
    id="JJ_003",
    query="How are children in conflict with law treated by police?",
    preferred=("Juvenile Justice Act 2015", "10"),
    acceptable=[("Juvenile Justice Act 2015", "10"), ("Juvenile Justice Act 2015", "12")],
    category_filter="women_child",
),

TestCase(
    id="JJ_004",
    query="What is juvenile justice board and what does it do?",
    preferred=("Juvenile Justice Act 2015", "8"),
    acceptable=[("Juvenile Justice Act 2015", "8"), ("Juvenile Justice Act 2015", "9")],
    category_filter="women_child",
),

TestCase(
    id="JJ_005",
    query="Can abandoned children be legally adopted?",
    preferred=("Juvenile Justice Act 2015", "56"),
    acceptable=[("Juvenile Justice Act 2015", "56"), ("Juvenile Justice Act 2015", "58")],
    category_filter="women_child",
),

TestCase(
    id="JJ_006",
    query="What rehabilitation is provided to juvenile offenders?",
    preferred=("Juvenile Justice Act 2015", "18"),
    acceptable=[("Juvenile Justice Act 2015", "18"), ("Juvenile Justice Act 2015", "19")],
    category_filter="women_child",
),

TestCase(
    id="POCSO_001",
    query="What is punishment for sexual assault on a child?",
    preferred=("Protection Of Children From Sexual Offences Act 2012", "8"),
    acceptable=[("Protection Of Children From Sexual Offences Act 2012", "8"), ("Protection Of Children From Sexual Offences Act 2012", "10")],
    category_filter="women_child",
),

TestCase(
    id="POCSO_002",
    query="school teacher suspects child abuse what is legal duty to report",
    preferred=("Protection Of Children From Sexual Offences Act 2012", "19"),
    acceptable=[("Protection Of Children From Sexual Offences Act 2012", "19"), ("Protection Of Children From Sexual Offences Act 2012", "21")],
    category_filter="women_child",
),

TestCase(
    id="POCSO_003",
    query="Is police required to register FIR in child abuse cases?",
    preferred=("Protection Of Children From Sexual Offences Act 2012", "19"),
    acceptable=[("Protection Of Children From Sexual Offences Act 2012", "19")],
    category_filter="women_child",
),

TestCase(
    id="POCSO_004",
    query="What protection is given to child victim during trial?",
    preferred=("Protection Of Children From Sexual Offences Act 2012", "33"),
    acceptable=[("Protection Of Children From Sexual Offences Act 2012", "33"), ("Protection Of Children From Sexual Offences Act 2012", "36")],
    category_filter="women_child",
),

TestCase(
    id="POCSO_005",
    query="What is considered sexual harassment of a child?",
    preferred=("Protection Of Children From Sexual Offences Act 2012", "11"),
    acceptable=[("Protection Of Children From Sexual Offences Act 2012", "11")],
    category_filter="women_child",
),

TestCase(
    id="POCSO_006",
    query="Can media publish identity of child victim?",
    preferred=("Protection Of Children From Sexual Offences Act 2012", "23"),
    acceptable=[("Protection Of Children From Sexual Offences Act 2012", "23")],
    category_filter="women_child",
),

TestCase(
    id="DV_001",
    query="What can a woman do if she is facing domestic violence?",
    preferred=("Protection Of Women From Domestic Violence Act 2005", "12"),
    acceptable=[("Protection Of Women From Domestic Violence Act 2005", "12"), ("Protection Of Women From Domestic Violence Act 2005", "18")],
    category_filter="women_child",
),

TestCase(
    id="DV_002",
    query="How to file complaint under Domestic Violence Act?",
    preferred=("Protection Of Women From Domestic Violence Act 2005", "12"),
    acceptable=[("Protection Of Women From Domestic Violence Act 2005", "12")],
    category_filter="women_child",
),

TestCase(
    id="DV_003",
    query="What is domestic violence under law?",
    preferred=("Protection Of Women From Domestic Violence Act 2005", "3"),
    acceptable=[("Protection Of Women From Domestic Violence Act 2005", "3")],
    category_filter="women_child",
),

TestCase(
    id="DV_004",
    query="Can court order husband to provide residence to wife?",
    preferred=("Protection Of Women From Domestic Violence Act 2005", "19"),
    acceptable=[("Protection Of Women From Domestic Violence Act 2005", "19"), ("Protection Of Women From Domestic Violence Act 2005", "17")],
    category_filter="women_child",
),

TestCase(
    id="DV_005",
    query="What protection orders can be issued in domestic violence cases?",
    preferred=("Protection Of Women From Domestic Violence Act 2005", "18"),
    acceptable=[("Protection Of Women From Domestic Violence Act 2005", "18"), ("Protection Of Women From Domestic Violence Act 2005", "19")],
    category_filter="women_child",
),

TestCase(
    id="DV_006",
    query="Can live-in partner file domestic violence complaint?",
    preferred=("Protection Of Women From Domestic Violence Act 2005", "2"),
    acceptable=[("Protection Of Women From Domestic Violence Act 2005", "2"), ("Protection Of Women From Domestic Violence Act 2005", "12")],
    category_filter="women_child",
),

TestCase(
    id="POSH_001",
    query="What is considered sexual harassment at workplace?",
    preferred=("Sexual Harassment Of Women At Workplace Act 2013", "2"),
    acceptable=[("Sexual Harassment Of Women At Workplace Act 2013", "2")],
    category_filter="women_child",
),

TestCase(
    id="POSH_002",
    query="How can a woman file complaint against harassment at office?",
    preferred=("Sexual Harassment Of Women At Workplace Act 2013", "9"),
    acceptable=[("Sexual Harassment Of Women At Workplace Act 2013", "9"), ("Sexual Harassment Of Women At Workplace Act 2013", "10")],
    category_filter="women_child",
),

TestCase(
    id="POSH_003",
    query="What is Internal Complaints Committee in companies?",
    preferred=("Sexual Harassment Of Women At Workplace Act 2013", "4"),
    acceptable=[("Sexual Harassment Of Women At Workplace Act 2013", "4"), ("Sexual Harassment Of Women At Workplace Act 2013", "6")],
    category_filter="women_child",
),

TestCase(
    id="POSH_004",
    query="Can employer ignore sexual harassment complaint?",
    preferred=("Sexual Harassment Of Women At Workplace Act 2013", "19"),
    acceptable=[("Sexual Harassment Of Women At Workplace Act 2013", "19"), ("Sexual Harassment Of Women At Workplace Act 2013", "21")],
    category_filter="women_child",
),

TestCase(
    id="POSH_005",
    query="What is punishment for false sexual harassment complaint?",
    preferred=("Sexual Harassment Of Women At Workplace Act 2013", "14"),
    acceptable=[("Sexual Harassment Of Women At Workplace Act 2013", "14")],
    category_filter="women_child",
),

TestCase(
    id="POSH_006",
    query="Does POSH Act apply to contractual workers and interns?",
    preferred=("Sexual Harassment Of Women At Workplace Act 2013", "2"),
    acceptable=[("Sexual Harassment Of Women At Workplace Act 2013", "2"), ("Sexual Harassment Of Women At Workplace Act 2013", "3")],
    category_filter="women_child",
),

TestCase(
    id="EPF_001",
    query="How much contribution does employer and employee make to PF?",
    preferred=("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "7"),
    acceptable=[
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "7"),
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "6A"),
    ],
    category_filter="labour",
    notes="Contribution rates for employer and employee.",
),

TestCase(
    id="EPF_002",
    query="When can I withdraw my provident fund money?",
    preferred=("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "Withdrawal"),
    acceptable=[
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "Withdrawal"),
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "68"),
    ],
    category_filter="labour",
    notes="Conditions for PF withdrawal.",
),

TestCase(
    id="EPF_003",
    query="What happens if employer does not deposit PF contribution?",
    preferred=("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "14B"),
    acceptable=[
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "14B"),
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "7Q"),
    ],
    category_filter="labour",
    notes="Damages and interest for default.",
),

TestCase(
    id="EPF_004",
    query="Is PF mandatory for all employees in India?",
    preferred=("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "1"),
    acceptable=[
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "1"),
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "2"),
    ],
    category_filter="labour",
    notes="Applicability of the Act.",
),

TestCase(
    id="EPF_005",
    query="Can I transfer PF when changing jobs?",
    preferred=("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "17"),
    acceptable=[
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "17"),
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "Transfer"),
    ],
    category_filter="labour",
    notes="Transfer of PF account.",
),

TestCase(
    id="EPF_006",
    query="What are penalties for non-compliance under PF law?",
    preferred=("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "14"),
    acceptable=[
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "14"),
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "14A"),
    ],
    category_filter="labour",
    notes="Offences and penalties.",
),

TestCase(
    id="EPF_007",
    query="I changed jobs, what happens to my PF account?",
    preferred=("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "17"),
    acceptable=[
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "17"),
        ("The Employees Provident Funds And Miscellaneous Provisions Act 1952", "Transfer"),
    ],
    category_filter="labour",
    notes="Real-world job change scenario.",
),

TestCase(
    id="MBA_001",
    query="How many weeks of maternity leave are allowed in India?",
    preferred=("The Maternity Benefit Act 1961", "5"),
    acceptable=[
        ("The Maternity Benefit Act 1961", "5"),
        ("The Maternity Benefit Act 1961", "3"),
    ],
    category_filter="labour",
    notes="Duration of maternity leave.",
),

TestCase(
    id="MBA_002",
    query="Will I get salary during maternity leave?",
    preferred=("The Maternity Benefit Act 1961", "6"),
    acceptable=[
        ("The Maternity Benefit Act 1961", "6"),
        ("The Maternity Benefit Act 1961", "4"),
    ],
    category_filter="labour",
    notes="Maternity benefit payment.",
),

TestCase(
    id="MBA_003",
    query="Can employer fire a woman during pregnancy?",
    preferred=("The Maternity Benefit Act 1961", "12"),
    acceptable=[
        ("The Maternity Benefit Act 1961", "12"),
        ("The Maternity Benefit Act 1961", "21"),
    ],
    category_filter="labour",
    notes="Protection against dismissal.",
),

TestCase(
    id="MBA_004",
    query="Who is eligible for maternity benefits in a company?",
    preferred=("The Maternity Benefit Act 1961", "5"),
    acceptable=[
        ("The Maternity Benefit Act 1961", "5"),
        ("The Maternity Benefit Act 1961", "Eligibility"),
    ],
    category_filter="labour",
    notes="Eligibility conditions.",
),

TestCase(
    id="MBA_005",
    query="How do I apply for maternity leave officially?",
    preferred=("The Maternity Benefit Act 1961", "6"),
    acceptable=[
        ("The Maternity Benefit Act 1961", "6"),
        ("The Maternity Benefit Act 1961", "7"),
    ],
    category_filter="labour",
    notes="Procedure for claiming benefit.",
),

TestCase(
    id="MBA_006",
    query="Does maternity benefit apply to adoption cases?",
    preferred=("The Maternity Benefit Act 1961", "9A"),
    acceptable=[
        ("The Maternity Benefit Act 1961", "9A"),
        ("The Maternity Benefit Act 1961", "5"),
    ],
    category_filter="labour",
    notes="Adoption and commissioning mothers.",
),

TestCase(
    id="MBA_007",
    query="What happens if employer refuses maternity leave?",
    preferred=("The Maternity Benefit Act 1961", "21"),
    acceptable=[
        ("The Maternity Benefit Act 1961", "21"),
        ("The Maternity Benefit Act 1961", "12"),
    ],
    category_filter="labour",
    notes="Penalty/enforcement for violation.",
),

TestCase(
    id="BSA_001",
    query="Is WhatsApp chat admissible as evidence in court?",
    preferred=("Bharatiya Sakshya Adhiniyam 2023", "65"),
    acceptable=[
        ("Bharatiya Sakshya Adhiniyam 2023", "65"),
        ("Bharatiya Sakshya Adhiniyam 2023", "63"),
    ],
    category_filter="criminal",
    notes="Electronic records admissibility.",
),

TestCase(
    id="BSA_002",
    query="Can police use recorded phone calls as evidence?",
    preferred=("Bharatiya Sakshya Adhiniyam 2023", "65"),
    acceptable=[
        ("Bharatiya Sakshya Adhiniyam 2023", "65"),
        ("Bharatiya Sakshya Adhiniyam 2023", "59"),
    ],
    category_filter="criminal",
    notes="Audio recordings and admissibility.",
),

TestCase(
    id="BSA_003",
    query="Is a confession made to police valid in court?",
    preferred=("Bharatiya Sakshya Adhiniyam 2023", "23"),
    acceptable=[
        ("Bharatiya Sakshya Adhiniyam 2023", "23"),
        ("Bharatiya Sakshya Adhiniyam 2023", "24"),
    ],
    category_filter="criminal",
    notes="Confessions to police officer.",
),

TestCase(
    id="BSA_004",
    query="Who has the burden of proof in a criminal case?",
    preferred=("Bharatiya Sakshya Adhiniyam 2023", "101"),
    acceptable=[
        ("Bharatiya Sakshya Adhiniyam 2023", "101"),
        ("Bharatiya Sakshya Adhiniyam 2023", "102"),
    ],
    category_filter="criminal",
    notes="Burden of proof principle.",
),

TestCase(
    id="BSA_005",
    query="Can a statement given to magistrate be used as evidence?",
    preferred=("Bharatiya Sakshya Adhiniyam 2023", "164"),
    acceptable=[
        ("Bharatiya Sakshya Adhiniyam 2023", "164"),
        ("Bharatiya Sakshya Adhiniyam 2023", "26"),
    ],
    category_filter="criminal",
    notes="Magistrate-recorded statements.",
),

TestCase(
    id="BSA_006",
    query="Are electronic documents like emails valid evidence in court?",
    preferred=("Bharatiya Sakshya Adhiniyam 2023", "65"),
    acceptable=[
        ("Bharatiya Sakshya Adhiniyam 2023", "65"),
        ("Bharatiya Sakshya Adhiniyam 2023", "63"),
    ],
    category_filter="criminal",
    notes="Digital evidence validity.",
),

TestCase(
    id="BSA_007",
    query="Can silence of accused be used against them?",
    preferred=("Bharatiya Sakshya Adhiniyam 2023", "114"),
    acceptable=[
        ("Bharatiya Sakshya Adhiniyam 2023", "114"),
        ("Bharatiya Sakshya Adhiniyam 2023", "106"),
    ],
    category_filter="criminal",
    notes="Presumptions and inference rules.",
),

TestCase(
    id="BSA_008",
    query="What is primary evidence and secondary evidence difference?",
    preferred=("Bharatiya Sakshya Adhiniyam 2023", "62"),
    acceptable=[
        ("Bharatiya Sakshya Adhiniyam 2023", "62"),
        ("Bharatiya Sakshya Adhiniyam 2023", "63"),
    ],
    category_filter="criminal",
    notes="Types of documentary evidence.",
),

TestCase(
    id="BSA_009",
    query="Can a family member be forced to testify in court?",
    preferred=("Bharatiya Sakshya Adhiniyam 2023", "118"),
    acceptable=[
        ("Bharatiya Sakshya Adhiniyam 2023", "118"),
        ("Bharatiya Sakshya Adhiniyam 2023", "120"),
    ],
    category_filter="criminal",
    notes="Witness competency and compulsion.",
),

TestCase(
    id="BSA_010",
    query="Is CCTV footage accepted as legal proof in criminal cases?",
    preferred=("Bharatiya Sakshya Adhiniyam 2023", "65"),
    acceptable=[
        ("Bharatiya Sakshya Adhiniyam 2023", "65"),
        ("Bharatiya Sakshya Adhiniyam 2023", "63"),
    ],
    category_filter="criminal",
    notes="Video evidence admissibility.",
),

TestCase(
    id="GWA_001",
    query="How can I become legal guardian of a child in India?",
    preferred=("Guardians And Wards Act 1890", "7"),
    acceptable=[
        ("Guardians And Wards Act 1890", "7"),
        ("Guardians And Wards Act 1890", "8"),
    ],
    category_filter="family",
    notes="Appointment of guardian procedure.",
),

TestCase(
    id="GWA_002",
    query="Can a court appoint guardian without parents consent?",
    preferred=("Guardians And Wards Act 1890", "7"),
    acceptable=[
        ("Guardians And Wards Act 1890", "7"),
        ("Guardians And Wards Act 1890", "17"),
    ],
    category_filter="family",
    notes="Court-appointed guardianship.",
),

TestCase(
    id="GWA_003",
    query="Who can file petition for child custody in court?",
    preferred=("Guardians And Wards Act 1890", "10"),
    acceptable=[
        ("Guardians And Wards Act 1890", "10"),
        ("Guardians And Wards Act 1890", "7"),
    ],
    category_filter="family",
    notes="Eligibility to apply for guardianship.",
),

TestCase(
    id="GWA_004",
    query="Can grandparents become legal guardians of a minor?",
    preferred=("Guardians And Wards Act 1890", "7"),
    acceptable=[
        ("Guardians And Wards Act 1890", "7"),
        ("Guardians And Wards Act 1890", "17"),
    ],
    category_filter="family",
    notes="Eligibility of relatives.",
),

TestCase(
    id="GWA_005",
    query="What factors does court consider in child custody cases?",
    preferred=("Guardians And Wards Act 1890", "17"),
    acceptable=[
        ("Guardians And Wards Act 1890", "17"),
        ("Guardians And Wards Act 1890", "7"),
    ],
    category_filter="family",
    notes="Welfare of child principle.",
),

TestCase(
    id="GWA_006",
    query="How to remove a legal guardian in India?",
    preferred=("Guardians And Wards Act 1890", "39"),
    acceptable=[
        ("Guardians And Wards Act 1890", "39"),
        ("Guardians And Wards Act 1890", "7"),
    ],
    category_filter="family",
    notes="Removal of guardian.",
),

TestCase(
    id="HMA_001",
    query="What are the legal requirements for a valid Hindu marriage?",
    preferred=("Hindu Marriage Act 1955", "5"),
    acceptable=[
        ("Hindu Marriage Act 1955", "5"),
        ("Hindu Marriage Act 1955", "7"),
    ],
    category_filter="family",
    notes="Conditions of valid marriage.",
),

TestCase(
    id="HMA_002",
    query="How can I file for divorce under Hindu Marriage Act?",
    preferred=("Hindu Marriage Act 1955", "13"),
    acceptable=[
        ("Hindu Marriage Act 1955", "13"),
        ("Hindu Marriage Act 1955", "13B"),
    ],
    category_filter="family",
    notes="Divorce grounds and mutual consent.",
),

TestCase(
    id="HMA_003",
    query="Can I remarry without getting divorce first?",
    preferred=("Hindu Marriage Act 1955", "11"),
    acceptable=[
        ("Hindu Marriage Act 1955", "11"),
        ("Hindu Marriage Act 1955", "5"),
    ],
    category_filter="family",
    notes="Bigamy invalidity.",
),

TestCase(
    id="HMA_004",
    query="What is cruelty as a ground for divorce?",
    preferred=("Hindu Marriage Act 1955", "13"),
    acceptable=[
        ("Hindu Marriage Act 1955", "13"),
        ("Hindu Marriage Act 1955", "10"),
    ],
    category_filter="family",
    notes="Divorce on cruelty ground.",
),

TestCase(
    id="HMA_005",
    query="How long does mutual divorce take in India?",
    preferred=("Hindu Marriage Act 1955", "13B"),
    acceptable=[
        ("Hindu Marriage Act 1955", "13B"),
        ("Hindu Marriage Act 1955", "13"),
    ],
    category_filter="family",
    notes="Mutual consent divorce timeline.",
),

TestCase(
    id="HMA_006",
    query="Can wife claim maintenance after separation?",
    preferred=("Hindu Marriage Act 1955", "24"),
    acceptable=[
        ("Hindu Marriage Act 1955", "24"),
        ("Hindu Marriage Act 1955", "25"),
    ],
    category_filter="family",
    notes="Maintenance pendente lite.",
),

TestCase(
    id="HMA_007",
    query="Is live-in relationship considered marriage under Hindu law?",
    preferred=("Hindu Marriage Act 1955", "5"),
    acceptable=[
        ("Hindu Marriage Act 1955", "5"),
        ("Hindu Marriage Act 1955", "7"),
    ],
    category_filter="family",
    notes="Marriage validity ambiguity.",
),

TestCase(
    id="HSA_001",
    query="Who inherits property after a Hindu male dies without a will?",
    preferred=("Hindu Succession Act 1956", "8"),
    acceptable=[
        ("Hindu Succession Act 1956", "8"),
        ("Hindu Succession Act 1956", "9"),
    ],
    category_filter="family",
    notes="Intestate succession rules.",
),

TestCase(
    id="HSA_002",
    query="Do daughters have equal rights in ancestral property?",
    preferred=("Hindu Succession Act 1956", "6"),
    acceptable=[
        ("Hindu Succession Act 1956", "6"),
        ("Hindu Succession Act 1956", "8"),
    ],
    category_filter="family",
    notes="Daughter inheritance rights.",
),

TestCase(
    id="HSA_003",
    query="Can a daughter claim father's property after marriage?",
    preferred=("Hindu Succession Act 1956", "6"),
    acceptable=[
        ("Hindu Succession Act 1956", "6"),
        ("Hindu Succession Act 1956", "8"),
    ],
    category_filter="family",
    notes="Married daughter's rights.",
),

TestCase(
    id="HSA_004",
    query="What happens if someone dies without legal heirs?",
    preferred=("Hindu Succession Act 1956", "29"),
    acceptable=[
        ("Hindu Succession Act 1956", "29"),
        ("Hindu Succession Act 1956", "30"),
    ],
    category_filter="family",
    notes="Escheat to government.",
),

TestCase(
    id="HSA_005",
    query="Can a will override Hindu succession rules?",
    preferred=("Hindu Succession Act 1956", "30"),
    acceptable=[
        ("Hindu Succession Act 1956", "30"),
        ("Hindu Succession Act 1956", "8"),
    ],
    category_filter="family",
    notes="Testamentary succession.",
),

TestCase(
    id="HSA_006",
    query="Who are class 1 heirs under Hindu succession law?",
    preferred=("Hindu Succession Act 1956", "8"),
    acceptable=[
        ("Hindu Succession Act 1956", "8"),
        ("Hindu Succession Act 1956", "9"),
    ],
    category_filter="family",
    notes="Heir classification.",
),

TestCase(
    id="ISA_001",
    query="How is property distributed when someone dies without a will?",
    preferred=("Indian Succession Act 1925", "33"),
    acceptable=[
        ("Indian Succession Act 1925", "33"),
        ("Indian Succession Act 1925", "32"),
    ],
    category_filter="family",
    notes="Intestate succession (non-Hindu).",
),

TestCase(
    id="ISA_002",
    query="What is a legal will and how do I make one valid?",
    preferred=("Indian Succession Act 1925", "63"),
    acceptable=[
        ("Indian Succession Act 1925", "63"),
        ("Indian Succession Act 1925", "59"),
    ],
    category_filter="family",
    notes="Execution of will.",
),

TestCase(
    id="ISA_003",
    query="Can a person change their will after writing it?",
    preferred=("Indian Succession Act 1925", "70"),
    acceptable=[
        ("Indian Succession Act 1925", "70"),
        ("Indian Succession Act 1925", "63"),
    ],
    category_filter="family",
    notes="Revocation/amendment of will.",
),

TestCase(
    id="ISA_004",
    query="Who can be appointed as executor of a will?",
    preferred=("Indian Succession Act 1925", "222"),
    acceptable=[
        ("Indian Succession Act 1925", "222"),
        ("Indian Succession Act 1925", "230"),
    ],
    category_filter="family",
    notes="Executor appointment.",
),

TestCase(
    id="ISA_005",
    query="What happens if there is no nominee in bank account after death?",
    preferred=("Indian Succession Act 1925", "211"),
    acceptable=[
        ("Indian Succession Act 1925", "211"),
        ("Indian Succession Act 1925", "32"),
    ],
    category_filter="family",
    notes="Estate administration.",
),

TestCase(
    id="ISA_006",
    query="Is handwritten will legally valid in India?",
    preferred=("Indian Succession Act 1925", "63"),
    acceptable=[
        ("Indian Succession Act 1925", "63"),
        ("Indian Succession Act 1925", "59"),
    ],
    category_filter="family",
    notes="Holographic will validity.",
),

TestCase(
    id="SMA_001",
    query="How can two people from different religions get married legally?",
    preferred=("Special Marriage Act 1954", "4"),
    acceptable=[
        ("Special Marriage Act 1954", "4"),
        ("Special Marriage Act 1954", "5"),
    ],
    category_filter="family",
    notes="Interfaith marriage conditions.",
),

TestCase(
    id="SMA_002",
    query="What is the procedure for registering marriage under Special Marriage Act?",
    preferred=("Special Marriage Act 1954", "15"),
    acceptable=[
        ("Special Marriage Act 1954", "15"),
        ("Special Marriage Act 1954", "16"),
    ],
    category_filter="family",
    notes="Marriage registration process.",
),

TestCase(
    id="SMA_003",
    query="Is parental consent required for marriage under Special Marriage Act?",
    preferred=("Special Marriage Act 1954", "4"),
    acceptable=[
        ("Special Marriage Act 1954", "4"),
        ("Special Marriage Act 1954", "5"),
    ],
    category_filter="family",
    notes="Consent requirement.",
),

TestCase(
    id="SMA_004",
    query="Can I marry without religious ceremony under law?",
    preferred=("Special Marriage Act 1954", "11"),
    acceptable=[
        ("Special Marriage Act 1954", "11"),
        ("Special Marriage Act 1954", "4"),
    ],
    category_filter="family",
    notes="Civil marriage validity.",
),

TestCase(
    id="SMA_005",
    query="What is notice period before marriage registration?",
    preferred=("Special Marriage Act 1954", "5"),
    acceptable=[
        ("Special Marriage Act 1954", "5"),
        ("Special Marriage Act 1954", "6"),
    ],
    category_filter="family",
    notes="Notice requirement.",
),

TestCase(
    id="SMA_006",
    query="Can foreign nationals marry under Special Marriage Act in India?",
    preferred=("Special Marriage Act 1954", "4"),
    acceptable=[
        ("Special Marriage Act 1954", "4"),
        ("Special Marriage Act 1954", "18"),
    ],
    category_filter="family",
    notes="Cross-national applicability.",
),

TestCase(
    id="REG_001",
    query="Is it mandatory to register a sale deed in India?",
    preferred=("Registration Act 1908", "17"),
    acceptable=[
        ("Registration Act 1908", "17"),
        ("Registration Act 1908", "49"),
    ],
    category_filter="property",
    notes="Compulsory registration of documents.",
),

TestCase(
    id="REG_002",
    query="What happens if I don't register a property sale agreement?",
    preferred=("Registration Act 1908", "49"),
    acceptable=[
        ("Registration Act 1908", "49"),
        ("Registration Act 1908", "17"),
    ],
    category_filter="property",
    notes="Effect of non-registration.",
),

TestCase(
    id="REG_003",
    query="How long do I have to register a document after signing it?",
    preferred=("Registration Act 1908", "23"),
    acceptable=[
        ("Registration Act 1908", "23"),
        ("Registration Act 1908", "25"),
    ],
    category_filter="property",
    notes="Time limit for registration.",
),

TestCase(
    id="REG_004",
    query="Can an unregistered agreement be used as evidence in court?",
    preferred=("Registration Act 1908", "49"),
    acceptable=[
        ("Registration Act 1908", "49"),
        ("Registration Act 1908", "17"),
    ],
    category_filter="property",
    notes="Evidentiary value of unregistered documents.",
),

TestCase(
    id="REG_005",
    query="Which documents are compulsory to register under law?",
    preferred=("Registration Act 1908", "17"),
    acceptable=[
        ("Registration Act 1908", "17"),
        ("Registration Act 1908", "18"),
    ],
    category_filter="property",
    notes="List of compulsory registrable documents.",
),

TestCase(
    id="REG_006",
    query="Can a gift deed be valid without registration?",
    preferred=("Registration Act 1908", "17"),
    acceptable=[
        ("Registration Act 1908", "17"),
        ("Registration Act 1908", "49"),
    ],
    category_filter="property",
    notes="Registration requirement for gift deeds.",
),

TestCase(
    id="LSA_001",
    query="How can I get free legal aid in India?",
    preferred=("Legal Services Authorities Act 1987", "12"),
    acceptable=[
        ("Legal Services Authorities Act 1987", "12"),
        ("Legal Services Authorities Act 1987", "13"),
    ],
    category_filter="rights",
    notes="Eligibility for free legal services.",
),

TestCase(
    id="LSA_002",
    query="Who is eligible for free lawyer provided by government?",
    preferred=("Legal Services Authorities Act 1987", "12"),
    acceptable=[
        ("Legal Services Authorities Act 1987", "12"),
        ("Legal Services Authorities Act 1987", "11"),
    ],
    category_filter="rights",
    notes="Eligibility criteria for legal aid.",
),

TestCase(
    id="LSA_003",
    query="does government provide lawyer for domestic violence victim",
    preferred=("Legal Services Authorities Act 1987", "13"),
    acceptable=[
        ("Legal Services Authorities Act 1987", "13"),
        ("Legal Services Authorities Act 1987", "12"),
    ],
    category_filter="rights",
    notes="Procedure for applying legal aid.",
),

TestCase(
    id="LSA_004",
    query="can undertrial prisoner get free legal aid",
    preferred=("Legal Services Authorities Act 1987", "12"),
    acceptable=[
        ("Legal Services Authorities Act 1987", "12"),
        ("Legal Services Authorities Act 1987", "14"),
    ],
    category_filter="rights",
    notes="Scope of free legal services.",
),

TestCase(
    id="LSA_005",
    query="Can I get free lawyer if I cannot afford court fees?",
    preferred=("Legal Services Authorities Act 1987", "12"),
    acceptable=[
        ("Legal Services Authorities Act 1987", "12"),
        ("Legal Services Authorities Act 1987", "13"),
    ],
    category_filter="rights",
    notes="Economic eligibility condition.",
),

TestCase(
    id="LSA_006",
    query="What authorities provide legal aid in district courts?",
    preferred=("Legal Services Authorities Act 1987", "6"),
    acceptable=[
        ("Legal Services Authorities Act 1987", "6"),
        ("Legal Services Authorities Act 1987", "11"),
    ],
    category_filter="rights",
    notes="Legal Services Authorities structure.",
),

TestCase(
    id="RTI_001",
    query="How do I file an RTI application in India?",
    preferred=("Right To Information Act 2005", "6"),
    acceptable=[
        ("Right To Information Act 2005", "6"),
        ("Right To Information Act 2005", "7"),
    ],
    category_filter="rights",
    notes="Procedure to file RTI request.",
),

TestCase(
    id="RTI_002",
    query="What information can I request under RTI Act?",
    preferred=("Right To Information Act 2005", "2"),
    acceptable=[
        ("Right To Information Act 2005", "2"),
        ("Right To Information Act 2005", "8"),
    ],
    category_filter="rights",
    notes="Scope of information disclosure.",
),

TestCase(
    id="RTI_003",
    query="Can government refuse to give information under RTI?",
    preferred=("Right To Information Act 2005", "8"),
    acceptable=[
        ("Right To Information Act 2005", "8"),
        ("Right To Information Act 2005", "9"),
    ],
    category_filter="rights",
    notes="Exemptions from disclosure.",
),

TestCase(
    id="RTI_004",
    query="How much fee is required to file RTI application?",
    preferred=("Right To Information Act 2005", "6"),
    acceptable=[
        ("Right To Information Act 2005", "6"),
        ("Right To Information Act 2005", "7"),
    ],
    category_filter="rights",
    notes="Application fee rules.",
),

TestCase(
    id="RTI_005",
    query="What can I do if my RTI request is ignored?",
    preferred=("Right To Information Act 2005", "19"),
    acceptable=[
        ("Right To Information Act 2005", "19"),
        ("Right To Information Act 2005", "20"),
    ],
    category_filter="rights",
    notes="Appeal and complaint mechanism.",
),

TestCase(
    id="RTI_006",
    query="Is personal information of government employees available under RTI?",
    preferred=("Right To Information Act 2005", "8"),
    acceptable=[
        ("Right To Information Act 2005", "8"),
        ("Right To Information Act 2005", "11"),
    ],
    category_filter="rights",
    notes="Privacy vs disclosure balance.",
),

TestCase(
    id="MWPSC_001",
    query="Can parents legally claim maintenance from their children in India?",
    preferred=("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "4"),
    acceptable=[
        ("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "4"),
        ("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "5"),
    ],
    category_filter="social_justice",
    notes="Children's obligation to maintain parents.",
),

TestCase(
    id="MWPSC_002",
    query="How can senior citizens file for maintenance against their children?",
    preferred=("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "5"),
    acceptable=[
        ("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "5"),
        ("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "6"),
    ],
    category_filter="social_justice",
    notes="Procedure for claiming maintenance.",
),

TestCase(
    id="MWPSC_003",
    query="What rights do elderly parents have if children neglect them?",
    preferred=("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "4"),
    acceptable=[
        ("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "4"),
        ("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "9"),
    ],
    category_filter="social_justice",
    notes="Neglect and legal remedy.",
),

TestCase(
    id="MWPSC_004",
    query="Can property be transferred back if children don't take care of parents?",
    preferred=("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "23"),
    acceptable=[
        ("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "23"),
        ("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "4"),
    ],
    category_filter="social_justice",
    notes="Property transfer conditions.",
),

TestCase(
    id="MWPSC_005",
    query="Where can senior citizens complain about neglect by children?",
    preferred=("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "7"),
    acceptable=[
        ("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "7"),
        ("Maintenance And Welfare Of Parents And Senior Citizens Act 2007", "5"),
    ],
    category_filter="social_justice",
    notes="Tribunal/authority jurisdiction.",
),

TestCase(
    id="RPWD_001",
    query="What rights do disabled persons have in employment?",
    preferred=("Rights Of Persons With Disabilities Act 2016", "20"),
    acceptable=[
        ("Rights Of Persons With Disabilities Act 2016", "20"),
        ("Rights Of Persons With Disabilities Act 2016", "21"),
    ],
    category_filter="social_justice",
    notes="Non-discrimination in employment.",
),

TestCase(
    id="RPWD_002",
    query="Can a company refuse job to a person because of disability?",
    preferred=("Rights Of Persons With Disabilities Act 2016", "3"),
    acceptable=[
        ("Rights Of Persons With Disabilities Act 2016", "3"),
        ("Rights Of Persons With Disabilities Act 2016", "20"),
    ],
    category_filter="social_justice",
    notes="Prohibition of discrimination.",
),

TestCase(
    id="RPWD_003",
    query="What facilities must be provided for disabled persons in public buildings?",
    preferred=("Rights Of Persons With Disabilities Act 2016", "44"),
    acceptable=[
        ("Rights Of Persons With Disabilities Act 2016", "44"),
        ("Rights Of Persons With Disabilities Act 2016", "45"),
    ],
    category_filter="social_justice",
    notes="Accessibility requirements.",
),

TestCase(
    id="RPWD_004",
    query="How do I get disability certificate in India?",
    preferred=("Rights Of Persons With Disabilities Act 2016", "57"),
    acceptable=[
        ("Rights Of Persons With Disabilities Act 2016", "57"),
        ("Rights Of Persons With Disabilities Act 2016", "58"),
    ],
    category_filter="social_justice",
    notes="Certification process.",
),

TestCase(
    id="RPWD_005",
    query="Is reservation available for disabled persons in government jobs?",
    preferred=("Rights Of Persons With Disabilities Act 2016", "34"),
    acceptable=[
        ("Rights Of Persons With Disabilities Act 2016", "34"),
        ("Rights Of Persons With Disabilities Act 2016", "35"),
    ],
    category_filter="social_justice",
    notes="Reservation and quotas.",
),

TestCase(
    id="SCST_001",
    query="What is considered an offence under SC/ST Atrocities Act?",
    preferred=("Scheduled Castes And Scheduled Tribes Act 1989", "3"),
    acceptable=[
        ("Scheduled Castes And Scheduled Tribes Act 1989", "3"),
        ("Scheduled Castes And Scheduled Tribes Act 1989", "4"),
    ],
    category_filter="social_justice",
    notes="Definition of atrocities.",
),

TestCase(
    id="SCST_002",
    query="How can a victim file complaint under SC/ST Act?",
    preferred=("Scheduled Castes And Scheduled Tribes Act 1989", "9"),
    acceptable=[
        ("Scheduled Castes And Scheduled Tribes Act 1989", "9"),
        ("Scheduled Castes And Scheduled Tribes Act 1989", "10"),
    ],
    category_filter="social_justice",
    notes="Complaint procedure.",
),

TestCase(
    id="SCST_003",
    query="What punishment is given for caste-based abuse or discrimination?",
    preferred=("Scheduled Castes And Scheduled Tribes Act 1989", "3"),
    acceptable=[
        ("Scheduled Castes And Scheduled Tribes Act 1989", "3"),
        ("Scheduled Castes And Scheduled Tribes Act 1989", "4"),
    ],
    category_filter="social_justice",
    notes="Punishment for atrocities.",
),

TestCase(
    id="SCST_004",
    query="Can police refuse to register FIR in SC/ST cases?",
    preferred=("Scheduled Castes And Scheduled Tribes Act 1989", "4"),
    acceptable=[
        ("Scheduled Castes And Scheduled Tribes Act 1989", "4"),
        ("Scheduled Castes And Scheduled Tribes Act 1989", "9"),
    ],
    category_filter="social_justice",
    notes="Mandatory FIR provisions.",
),

TestCase(
    id="SCST_005",
    query="What protection is given to SC/ST victims during trial?",
    preferred=("Scheduled Castes And Scheduled Tribes Act 1989", "15"),
    acceptable=[
        ("Scheduled Castes And Scheduled Tribes Act 1989", "15"),
        ("Scheduled Castes And Scheduled Tribes Act 1989", "14"),
    ],
    category_filter="social_justice",
    notes="Witness protection and trial safeguards.",
),

TestCase(
    id="DPA_001",
    query="Is taking or giving dowry illegal in India?",
    preferred=("Dowry Prohibition Act 1961", "3"),
    acceptable=[
        ("Dowry Prohibition Act 1961", "3"),
        ("Dowry Prohibition Act 1961", "2"),
    ],
    category_filter="women_child",
    notes="Core prohibition of dowry.",
),

TestCase(
    id="DPA_002",
    query="What is the punishment for demanding dowry from bride's family?",
    preferred=("Dowry Prohibition Act 1961", "3"),
    acceptable=[
        ("Dowry Prohibition Act 1961", "3"),
        ("Dowry Prohibition Act 1961", "4"),
    ],
    category_filter="women_child",
    notes="Penalty for dowry demand.",
),

TestCase(
    id="DPA_003",
    query="How can I file complaint for dowry harassment?",
    preferred=("Dowry Prohibition Act 1961", "4"),
    acceptable=[
        ("Dowry Prohibition Act 1961", "4"),
        ("Dowry Prohibition Act 1961", "7"),
    ],
    category_filter="women_child",
    notes="Complaint mechanism and enforcement.",
),

TestCase(
    id="DPA_004",
    query="What counts as dowry under Indian law?",
    preferred=("Dowry Prohibition Act 1961", "2"),
    acceptable=[
        ("Dowry Prohibition Act 1961", "2"),
        ("Dowry Prohibition Act 1961", "3"),
    ],
    category_filter="women_child",
    notes="Definition of dowry.",
),

TestCase(
    id="FA_001",
    query="what is a factory under the factories act",
    preferred=("Labour Factories Act 1948", "2"),
    acceptable=[("Labour Factories Act 1948", "2")],
    category_filter="labour",
    notes="Core definition: factory, worker, occupier.",
),

TestCase(
    id="FA_002",
    query="how do I register a new factory with the government",
    preferred=("Labour Factories Act 1948", "6"),
    acceptable=[("Labour Factories Act 1948", "6"), ("Labour Factories Act 1948", "7")],
    category_filter="labour",
    notes="Approval, licensing, and notice requirements.",
),

TestCase(
    id="FA_003",
    query="duties of factory owner for worker safety",
    preferred=("Labour Factories Act 1948", "7A"),
    acceptable=[("Labour Factories Act 1948", "7A")],
    category_filter="labour",
    notes="General duties of occupier.",
),

TestCase(
    id="FA_004",
    query="can factory inspector enter and inspect premises",
    preferred=("Labour Factories Act 1948", "9"),
    acceptable=[("Labour Factories Act 1948", "9")],
    category_filter="labour",
    notes="Inspection and enforcement powers.",
),

TestCase(
    id="FA_005",
    query="factory is very dirty and not maintained properly",
    preferred=("Labour Factories Act 1948", "11"),
    acceptable=[("Labour Factories Act 1948", "11")],
    category_filter="labour",
    notes="Cleanliness requirements.",
),

TestCase(
    id="FA_006",
    query="factory workers exposed to dust and chemical fumes",
    preferred=("Labour Factories Act 1948", "14"),
    acceptable=[("Labour Factories Act 1948", "14")],
    category_filter="labour",
    notes="Dust, fumes, and hazardous exposure control.",
),

TestCase(
    id="FA_007",
    query="factory must provide drinking water and sanitation",
    preferred=("Labour Factories Act 1948", "18"),
    acceptable=[("Labour Factories Act 1948", "18"), ("Labour Factories Act 1948", "19")],
    category_filter="labour",
    notes="Basic welfare: drinking water and sanitation.",
),

TestCase(
    id="FA_008",
    query="unguarded machine caused worker injury in factory",
    preferred=("Labour Factories Act 1948", "21"),
    acceptable=[("Labour Factories Act 1948", "21")],
    category_filter="labour",
    notes="Fencing of machinery and safety guards.",
),

TestCase(
    id="FA_009",
    query="factory fire safety and emergency exit rules",
    preferred=("Labour Factories Act 1948", "38"),
    acceptable=[("Labour Factories Act 1948", "37"), ("Labour Factories Act 1948", "38")],
    category_filter="labour",
    notes="Fire safety and hazardous process precautions.",
),

TestCase(
    id="FA_010",
    query="maximum working hours per day in factory",
    preferred=("Labour Factories Act 1948", "54"),
    acceptable=[("Labour Factories Act 1948", "51"), ("Labour Factories Act 1948", "54")],
    category_filter="labour",
    notes="Daily and weekly working hour limits.",
),

TestCase(
    id="FA_011",
    query="overtime not paid at double rate in factory",
    preferred=("Labour Factories Act 1948", "59"),
    acceptable=[("Labour Factories Act 1948", "59")],
    category_filter="labour",
    notes="Overtime wage compensation rules.",
),

TestCase(
    id="FA_012",
    query="child labour working in factory below legal age",
    preferred=("Labour Factories Act 1948", "67"),
    acceptable=[("Labour Factories Act 1948", "67"), ("Labour Factories Act 1948", "71")],
    category_filter="labour",
    notes="Prohibition of child labour and limits on young workers.",
),

TestCase(
    id="TPA_001",
    query="landlord wants to evict me without notice",
    preferred=("Transfer Of Property Act 1882", "106"),
    acceptable=[("Transfer Of Property Act 1882", "106"), ("Transfer Of Property Act 1882", "111")],
    category_filter="property",
),

TestCase(
    id="TPA_002",
    query="tenant rights under rental agreement",
    preferred=("Transfer Of Property Act 1882", "108"),
    acceptable=[("Transfer Of Property Act 1882", "108"), ("Transfer Of Property Act 1882", "105")],
    category_filter="property",
),

TestCase(
    id="TPA_004",
    query="landlord entering rented house without permission",
    preferred=("Transfer Of Property Act 1882", "108"),
    acceptable=[("Transfer Of Property Act 1882", "108")],
    category_filter="property",
),

TestCase(
    id="TPA_005",
    query="repairs not done by landlord in rented property",
    preferred=("Transfer Of Property Act 1882", "108"),
    acceptable=[("Transfer Of Property Act 1882", "108")],
    category_filter="property",
),

TestCase(
    id="TPA_006",
    query="lease ended but tenant not vacating",
    preferred=("Transfer Of Property Act 1882", "111"),
    acceptable=[("Transfer Of Property Act 1882", "111"), ("Transfer Of Property Act 1882", "116")],
    category_filter="property",
),

TestCase(
    id="TPA_007",
    query="seller hid defects in property before sale",
    preferred=("Transfer Of Property Act 1882", "55"),
    acceptable=[("Transfer Of Property Act 1882", "55")],
    category_filter="property",
),

TestCase(
    id="TPA_008",
    query="mortgaged house redemption after loan repayment",
    preferred=("Transfer Of Property Act 1882", "60"),
    acceptable=[("Transfer Of Property Act 1882", "60")],
    category_filter="property",
),

TestCase(
    id="TPA_009",
    query="bank auctioning mortgaged property after default",
    preferred=("Transfer Of Property Act 1882", "69"),
    acceptable=[("Transfer Of Property Act 1882", "69"), ("Transfer Of Property Act 1882", "67")],
    category_filter="property",
),

TestCase(
    id="TPA_010",
    query="can co-owner sell his share in joint property",
    preferred=("Transfer Of Property Act 1882", "44"),
    acceptable=[("Transfer Of Property Act 1882", "44")],
    category_filter="property",
),

TestCase(
    id="TPA_011",
    query="gift deed cancellation or validity issues",
    preferred=("Transfer Of Property Act 1882", "126"),
    acceptable=[("Transfer Of Property Act 1882", "126"), ("Transfer Of Property Act 1882", "123")],
    category_filter="property",
),

TestCase(
    id="TPA_012",
    query="how to legally exchange property with another person",
    preferred=("Transfer Of Property Act 1882", "118"),
    acceptable=[("Transfer Of Property Act 1882", "118")],
    category_filter="property",
),

TestCase(
    id="COI_001",
    query="my online order was defective, where can I file a consumer complaint?",
    preferred=("Consumer Protection Act 2019", "35"),
    acceptable=[
        ("Consumer Protection Act 2019", "35"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_002",
    query="what is product liability if a pressure cooker explodes?",
    preferred=("Consumer Protection Act 2019", "83"),
    acceptable=[
        ("Consumer Protection Act 2019", "83"),
        ("Consumer Protection Act 2019", "84"),
        ("Consumer Protection Act 2019", "85"),
        ("Consumer Protection Act 2019", "86"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_003",
    query="can the government order a company to recall unsafe products?",
    preferred=("Consumer Protection Act 2019", "20"),
    acceptable=[
        ("Consumer Protection Act 2019", "20"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_004",
    query="fake celebrity ad misled me into buying a product",
    preferred=("Consumer Protection Act 2019", "21"),
    acceptable=[
        ("Consumer Protection Act 2019", "21"),
        ("Consumer Protection Act 2019", "89"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_005",
    query="how do i appeal against district consumer commission order",
    preferred=("Consumer Protection Act 2019", "41"),
    acceptable=[
        ("Consumer Protection Act 2019", "41"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_006",
    query="can my consumer case be settled through mediation instead of trial",
    preferred=("Consumer Protection Act 2019", "37"),
    acceptable=[
        ("Consumer Protection Act 2019", "37"),
        ("Consumer Protection Act 2019", "79"),
        ("Consumer Protection Act 2019", "80"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_007",
    query="who counts as a consumer under the act?",
    preferred=("Consumer Protection Act 2019", "2"),
    acceptable=[
        ("Consumer Protection Act 2019", "2"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_008",
    query="seller refused refund for defective item after purchase",
    preferred=("Consumer Protection Act 2019", "39"),
    acceptable=[
        ("Consumer Protection Act 2019", "39"),
        ("Consumer Protection Act 2019", "35"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_010",
    query="district commission jurisdiction based on claim amount",
    preferred=("Consumer Protection Act 2019", "34"),
    acceptable=[
        ("Consumer Protection Act 2019", "34"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_021",
    query="A celebrity promoted a health drink with false claims and I suffered losses. Can action be taken against misleading advertisements?",
    preferred=("Consumer Protection Act 2019", "21"),
    acceptable=[
        ("Consumer Protection Act 2019", "18"),
        ("Consumer Protection Act 2019", "89"),
    ],
    category_filter="consumer",
),
TestCase(
    id="COI_022",
    query="shop is giving false discounts to customers",
    preferred=("Consumer Protection Act 2019", "21"),
    acceptable=[
        ("Consumer Protection Act 2019", "21"),
        ("Consumer Protection Act 2019", "19"),
        ("Consumer Protection Act 2019", "2"),
    ],
    category_filter="consumer",
),
TestCase(
    id="COI_023",
    query="internet provider is not providing promised service",
    preferred=("Consumer Protection Act 2019", "35"),
    acceptable=[
        ("Consumer Protection Act 2019", "35"),
        ("Consumer Protection Act 2019", "39"),
    ],
    category_filter="consumer",
),
TestCase(
    id="COI_024",
    query="hospital negligence consumer complaint",
    preferred=("Consumer Protection Act 2019", "35"),
    acceptable=[
        ("Consumer Protection Act 2019", "35"),
        ("Consumer Protection Act 2019", "39"),
    ],
    category_filter="consumer",
),
TestCase(
    id="COI_025",
    query="I was injured because a pressure cooker exploded due to a manufacturing defect. Can I sue the manufacturer directly?",
    preferred=("Consumer Protection Act 2019", "82"),
    acceptable=[
        ("Consumer Protection Act 2019", "83"),
        ("Consumer Protection Act 2019", "84"),
        ("Consumer Protection Act 2019", "2(34)")
    ],
    category_filter="consumer",
),
TestCase(
    id="COI_026",
    query="product warranty was denied by the company",
    preferred=("Consumer Protection Act 2019", "35"),
    acceptable=[
        ("Consumer Protection Act 2019", "35"),
        ("Consumer Protection Act 2019", "39"),
    ],
    category_filter="consumer",
),
TestCase(
    id="COI_027",
    query="restaurant served spoiled food",
    preferred=("Consumer Protection Act 2019", "35"),
    acceptable=[
        ("Consumer Protection Act 2019", "35"),
        ("Consumer Protection Act 2019", "39"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_011",
    query="is it legal to sell rice using an unstamped weighing machine?",
    preferred=("Legal Metrology Act 2009", "33"),
    acceptable=[
        ("Legal Metrology Act 2009", "33"),
        ("Legal Metrology Act 2009", "24"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_012",
    query="shopkeeper is using faulty weighing scale what law applies",
    preferred=("Legal Metrology Act 2009", "25"),
    acceptable=[
        ("Legal Metrology Act 2009", "25"),
        ("Legal Metrology Act 2009", "33"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_013",
    query="what details must be printed on packaged goods?",
    preferred=("Legal Metrology Act 2009", "18"),
    acceptable=[
        ("Legal Metrology Act 2009", "18"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_014",
    query="can legal metrology officer inspect my warehouse",
    preferred=("Legal Metrology Act 2009", "15"),
    acceptable=[
        ("Legal Metrology Act 2009", "15"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_015",
    query="do importers of weighing machines need registration",
    preferred=("Legal Metrology Act 2009", "19"),
    acceptable=[
        ("Legal Metrology Act 2009", "19"),
        ("Legal Metrology Act 2009", "38"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_016",
    query="penalty for manufacturing weighing machines without registration",
    preferred=("Legal Metrology Act 2009", "45"),
    acceptable=[
        ("Legal Metrology Act 2009", "45"),
        ("Legal Metrology Act 2009", "23"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_017",
    query="can prices be displayed in pounds instead of kilograms in india",
    preferred=("Legal Metrology Act 2009", "11"),
    acceptable=[
        ("Legal Metrology Act 2009", "11"),
        ("Legal Metrology Act 2009", "29"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_018",
    query="i bought only 900g instead of 1kg what offence is this",
    preferred=("Legal Metrology Act 2009", "34"),
    acceptable=[
        ("Legal Metrology Act 2009", "34"),
        ("Legal Metrology Act 2009", "30"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_019",
    query="weight machine verification expired... is that a violation?",
    preferred=("Legal Metrology Act 2009", "24"),
    acceptable=[
        ("Legal Metrology Act 2009", "24"),
        ("Legal Metrology Act 2009", "33"),
    ],
    category_filter="consumer",
),

TestCase(
    id="COI_020",
    query="can i appeal against an order under the legal metrology act?",
    preferred=("Legal Metrology Act 2009", "50"),
    acceptable=[
        ("Legal Metrology Act 2009", "50"),
    ],
    category_filter="consumer",
),

TestCase(
    id="LAB_WAGE_001",
    query="my company is paying me less than the minimum wage",
    preferred=("Code On Wages 2019", "6"),
    acceptable=[
        ("Code On Wages 2019", "6"),
        ("Code On Wages 2019", "5"),
    ],
    category_filter="labour",
    notes="Minimum wage entitlement.",
),

TestCase(
    id="LAB_WAGE_002",
    query="my employer pays me below the government minimum wage",
    preferred=("Code On Wages 2019", "6"),
    acceptable=[
        ("Code On Wages 2019", "6"),
    ],
    category_filter="labour",
    notes="Paraphrase.",
),

TestCase(
    id="LAB_WAGE_003",
    query="women in my office are paid less than men for the same work",
    preferred=("Code On Wages 2019", "3"),
    acceptable=[
        ("Code On Wages 2019", "3"),
    ],
    category_filter="labour",
    notes="Equal remuneration.",
),

TestCase(
    id="LAB_WAGE_004",
    query="can an employer pay female employees less than male employees",
    preferred=("Code On Wages 2019", "3"),
    acceptable=[
        ("Code On Wages 2019", "3"),
    ],
    category_filter="labour",
    notes="Question form.",
),

TestCase(
    id="LAB_WAGE_005",
    query="my employer has not paid my salary for three months",
    preferred=("Code On Wages 2019", "17"),
    acceptable=[
        ("Code On Wages 2019", "17"),
        ("Code On Wages 2019", "45"),
    ],
    category_filter="labour",
    notes="Delayed payment of wages.",
),

TestCase(
    id="LAB_WAGE_006",
    query="salary was not credited on the scheduled payday",
    preferred=("Code On Wages 2019", "17"),
    acceptable=[
        ("Code On Wages 2019", "17"),
    ],
    category_filter="labour",
    notes="Paraphrase.",
),

TestCase(
    id="LAB_WAGE_007",
    query="my employer deducted money from my salary without any reason",
    preferred=("Code On Wages 2019", "18"),
    acceptable=[
        ("Code On Wages 2019", "18"),
        ("Code On Wages 2019", "19"),
    ],
    category_filter="labour",
    notes="Unauthorized deductions.",
),

TestCase(
    id="LAB_WAGE_008",
    query="why was money deducted from my paycheck without explanation",
    preferred=("Code On Wages 2019", "18"),
    acceptable=[
        ("Code On Wages 2019", "18"),
    ],
    category_filter="labour",
    notes="Question form.",
),

TestCase(
    id="LAB_WAGE_009",
    query="i worked overtime but my employer did not pay extra wages",
    preferred=("Code On Wages 2019", "14"),
    acceptable=[
        ("Code On Wages 2019", "14"),
    ],
    category_filter="labour",
    notes="Overtime wages.",
),

TestCase(
    id="LAB_WAGE_010",
    query="worked extra hours but got normal salary only",
    preferred=("Code On Wages 2019", "14"),
    acceptable=[
        ("Code On Wages 2019", "14"),
    ],
    category_filter="labour",
    notes="Conversational.",
),

TestCase(
    id="NDPS_001",
    query="caught with illegal drugs for the first time",
    preferred=("Narcotic Drugs And Psychotropic Substances Act 1985", "21"),
    acceptable=[
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "21"),
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "22"),
    ],
    category_filter="criminal",
),

TestCase(
    id="NDPS_002",
    query="caught with illegal drugs or narcotics",
    preferred=("Narcotic Drugs And Psychotropic Substances Act 1985", "21"),
    acceptable=[
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "20"),
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "21"),
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "22"),
    ],
    category_filter="criminal",
    notes="Core possession/consumption/possession for sale cluster.",
),

TestCase(
    id="NDPS_003",
    query="drug trafficking or selling narcotics punishment",
    preferred=("Narcotic Drugs And Psychotropic Substances Act 1985", "21"),
    acceptable=[
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "21"),
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "27A"),
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "29"),
    ],
    category_filter="criminal",
    notes="Trafficking, commercial supply, abetment.",
),

TestCase(
    id="NDPS_004",
    query="police search and seizure in drug cases without warrant",
    preferred=("Narcotic Drugs And Psychotropic Substances Act 1985", "42"),
    acceptable=[
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "42"),
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "43"),
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "50"),
    ],
    category_filter="criminal",
    notes="Search powers and procedural safeguards.",
),

TestCase(
    id="NDPS_005",
    query="bail rules in NDPS cases",
    preferred=("Narcotic Drugs And Psychotropic Substances Act 1985", "37"),
    acceptable=[
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "37"),
    ],
    category_filter="criminal",
    notes="Strict bail conditions under NDPS.",
),

TestCase(
    id="NDPS_006",
    query="drug addict seeking treatment instead of punishment",
    preferred=("Narcotic Drugs And Psychotropic Substances Act 1985", "64A"),
    acceptable=[
        ("Narcotic Drugs And Psychotropic Substances Act 1985", "64A"),
    ],
    category_filter="criminal",
    notes="Immunity/rehabilitation for addicts.",
),

TestCase(
    id="ARMS_001",
    query="possessing or carrying firearm without licence",
    preferred=("The Arms Act 1959", "25"),
    acceptable=[
        ("The Arms Act 1959", "25"),
        ("The Arms Act 1959", "3"),
    ],
    category_filter="criminal",
    notes="Core offence: illegal possession/ownership.",
),

TestCase(
    id="ARMS_002",
    query="how to obtain firearm licence or legal requirement",
    preferred=("The Arms Act 1959", "3"),
    acceptable=[
        ("The Arms Act 1959", "3"),
        ("The Arms Act 1959", "14"),
    ],
    category_filter="criminal",
    notes="Licence requirement and application basis.",
),

TestCase(
    id="ARMS_003",
    query="firearm licence rejected or cancelled by authorities",
    preferred=("The Arms Act 1959", "14"),
    acceptable=[
        ("The Arms Act 1959", "14"),
        ("The Arms Act 1959", "17"),
        ("The Arms Act 1959", "18"),
    ],
    category_filter="criminal",
    notes="Refusal, suspension, cancellation and appeal cluster.",
),
TestCase(
    id="ARMS_004",
    query="using firearm during an offence punishment",
    preferred=("The Arms Act 1959", "27"),
    acceptable=[
        ("The Arms Act 1959", "27"),
    ],
    category_filter="criminal",
    notes="Aggravated offence involving firearms.",
),

TestCase(
    id="ARMS_005",
    query="importing or transferring firearms rules and licence",
    preferred=("The Arms Act 1959", "10"),
    acceptable=[
        ("The Arms Act 1959", "10"),
        ("The Arms Act 1959", "11"),
    ],
    category_filter="criminal",
    notes="Import/export and transfer control.",
),

TestCase(
    id="COI_001",
    query="right to equality under constitution",
    preferred=("Constitution Of India", "14"),
    acceptable=[("Constitution Of India", "14")],
    category_filter="constitution",
),

TestCase(
    id="COI_002",
    query="is untouchability banned in india",
    preferred=("Constitution Of India", "17"),
    acceptable=[("Constitution Of India", "17")],
    category_filter="constitution",
),

TestCase(
    id="COI_003",
    query="right to education for children",
    preferred=("Constitution Of India", "21A"),
    acceptable=[("Constitution Of India", "21A")],
    category_filter="constitution",
),

TestCase(
    id="COI_004",
    query="freedom of speech in india",
    preferred=("Constitution Of India", "19"),
    acceptable=[("Constitution Of India", "19")],
    category_filter="constitution",
),

TestCase(
    id="COI_005",
    query="right to life and personal liberty",
    preferred=("Constitution Of India", "21"),
    acceptable=[("Constitution Of India", "21")],
    category_filter="constitution",
),

TestCase(
    id="COI_006",
    query="freedom of religion in india",
    preferred=("Constitution Of India", "25"),
    acceptable=[("Constitution Of India", "25")],
    category_filter="constitution",
),

TestCase(
    id="COI_007",
    query="can i approach supreme court for fundamental rights violation",
    preferred=("Constitution Of India", "32"),
    acceptable=[("Constitution Of India", "32")],
    category_filter="constitution",
),

TestCase(
    id="COI_008",
    query="does every state have high court",
    preferred=("Constitution Of India", "214"),
    acceptable=[("Constitution Of India", "214")],
    category_filter="constitution",
),

TestCase(
    id="COI_009",
    query="official language of india",
    preferred=("Constitution Of India", "343"),
    acceptable=[("Constitution Of India", "343")],
    category_filter="constitution",
),

TestCase(
    id="COI_010",
    query="constitutional head of india",
    preferred=("Constitution Of India", "52"),
    acceptable=[("Constitution Of India", "52")],
    category_filter="constitution",
),

TestCase(
    id="COI_011",
    query="constitutional status of jammu and kashmir",
    preferred=("Constitution Of India", "370"),
    acceptable=[("Constitution Of India", "370")],
    category_filter="constitution",
),

TestCase(
    id="ITA_001",
    query="someone hacked my email account",
    preferred=("Information Technology Act 2000", "66"),
    acceptable=[("Information Technology Act 2000", "66"), ("Information Technology Act 2000", "43")],
    category_filter="cyber",
),

TestCase(
    id="ITA_002",
    query="unauthorized access to my computer or files",
    preferred=("Information Technology Act 2000", "43"),
    acceptable=[("Information Technology Act 2000", "43"), ("Information Technology Act 2000", "66")],
    category_filter="cyber",
),

TestCase(
    id="ITA_003",
    query="someone created fake profile using my identity",
    preferred=("Information Technology Act 2000", "66C"),
    acceptable=[("Information Technology Act 2000", "66C"), ("Information Technology Act 2000", "66D")],
    category_filter="cyber",
),

TestCase(
    id="ITA_004",
    query="online impersonation and cheating using my identity",
    preferred=("Information Technology Act 2000", "66D"),
    acceptable=[("Information Technology Act 2000", "66D"), ("Information Technology Act 2000", "66C")],
    category_filter="cyber",
),

TestCase(
    id="ITA_005",
    query="my personal data or photos were leaked online without consent",
    preferred=("Information Technology Act 2000", "43A"),
    acceptable=[("Information Technology Act 2000", "43A"), ("Information Technology Act 2000", "72"), ("Information Technology Act 2000", "72A")],
    category_filter="cyber",
),

TestCase(
    id="ITA_006",
    query="phishing or online banking fraud",
    preferred=("Information Technology Act 2000", "66D"),
    acceptable=[("Information Technology Act 2000", "66D"), ("Information Technology Act 2000", "66C")],
    category_filter="cyber",
),

TestCase(
    id="ITA_007",
    query="identity theft using OTP or stolen credentials",
    preferred=("Information Technology Act 2000", "66C"),
    acceptable=[("Information Technology Act 2000", "66C"), ("Information Technology Act 2000", "66D")],
    category_filter="cyber",
),

TestCase(
    id="ITA_008",
    query="website hosting obscene or illegal content",
    preferred=("Information Technology Act 2000", "67"),
    acceptable=[("Information Technology Act 2000", "67"), ("Information Technology Act 2000", "67A")],
    category_filter="cyber",
),

TestCase(
    id="ITA_009",
    query="government blocking or restricting a website",
    preferred=("Information Technology Act 2000", "69A"),
    acceptable=[("Information Technology Act 2000", "69A")],
    category_filter="cyber",
),

TestCase(
    id="ITA_010",
    query="is electronic contract valid without physical signature",
    preferred=("Information Technology Act 2000", "10A"),
    acceptable=[("Information Technology Act 2000", "10A"), ("Information Technology Act 2000", "4")],
    category_filter="cyber",
),

TestCase(
    id="ITA_011",
    query="fake digital signature or forged certificate",
    preferred=("Information Technology Act 2000", "73"),
    acceptable=[("Information Technology Act 2000", "73"), ("Information Technology Act 2000", "74")],
    category_filter="cyber",
),

TestCase(
    id="MVA_001",
    query="What should I do immediately after a road accident in India?",
    preferred=("Motor Vehicles Act 1988", "134"),
    acceptable=[
        ("Motor Vehicles Act 1988", "134"),
        ("Motor Vehicles Act 1988", "160"),
    ],
    category_filter="transport",
    notes="Duties after accident and reporting.",
),

TestCase(
    id="MVA_002",
    query="Is driving without a license a punishable offence?",
    preferred=("Motor Vehicles Act 1988", "181"),
    acceptable=[
        ("Motor Vehicles Act 1988", "181"),
        ("Motor Vehicles Act 1988", "3"),
    ],
    category_filter="transport",
    notes="Penalty for unlicensed driving.",
),

TestCase(
    id="MVA_003",
    query="What is the penalty for drunk driving in India?",
    preferred=("Motor Vehicles Act 1988", "185"),
    acceptable=[
        ("Motor Vehicles Act 1988", "185"),
        ("Motor Vehicles Act 1988", "184"),
    ],
    category_filter="transport",
    notes="Drunk driving punishment.",
),

TestCase(
    id="MVA_004",
    query="Do I need insurance for my vehicle?",
    preferred=("Motor Vehicles Act 1988", "146"),
    acceptable=[
        ("Motor Vehicles Act 1988", "146"),
        ("Motor Vehicles Act 1988", "147"),
    ],
    category_filter="transport",
    notes="Mandatory third-party insurance.",
),

TestCase(
    id="MVA_005",
    query="What happens if I drive without insurance?",
    preferred=("Motor Vehicles Act 1988", "196"),
    acceptable=[
        ("Motor Vehicles Act 1988", "196"),
        ("Motor Vehicles Act 1988", "146"),
    ],
    category_filter="transport",
    notes="Penalty for uninsured vehicle.",
),

TestCase(
    id="MVA_006",
    query="How do I get a driving license in India?",
    preferred=("Motor Vehicles Act 1988", "9"),
    acceptable=[
        ("Motor Vehicles Act 1988", "9"),
        ("Motor Vehicles Act 1988", "10"),
    ],
    category_filter="transport",
    notes="Driving license procedure.",
),

TestCase(
    id="MVA_007",
    query="Can I drive without wearing a helmet or seatbelt?",
    preferred=("Motor Vehicles Act 1988", "194B"),
    acceptable=[
        ("Motor Vehicles Act 1988", "194B"),
        ("Motor Vehicles Act 1988", "128"),
    ],
    category_filter="transport",
    notes="Safety equipment rules.",
),

TestCase(
    id="MVA_008",
    query="What are the speed limit rules for vehicles?",
    preferred=("Motor Vehicles Act 1988", "112"),
    acceptable=[
        ("Motor Vehicles Act 1988", "112"),
        ("Motor Vehicles Act 1988", "183"),
    ],
    category_filter="transport",
    notes="Speed regulation.",
),

TestCase(
    id="MVA_009",
    query="Can police seize my vehicle for traffic violations?",
    preferred=("Motor Vehicles Act 1988", "207"),
    acceptable=[
        ("Motor Vehicles Act 1988", "207"),
        ("Motor Vehicles Act 1988", "183"),
    ],
    category_filter="transport",
    notes="Seizure and enforcement powers.",
),

TestCase(
    id="MVA_010",
    query="What is the rule for hit and run accident cases?",
    preferred=("Motor Vehicles Act 1988", "161"),
    acceptable=[
        ("Motor Vehicles Act 1988", "161"),
        ("Motor Vehicles Act 1988", "166"),
    ],
    category_filter="transport",
    notes="Compensation for hit-and-run cases.",
),
TestCase(
    id="PA_001",
    query="how do I apply for a passport",
    preferred=("The Passports Act 1967", "5"),
    acceptable=[("The Passports Act 1967", "5")],
    category_filter="administrative",
),

TestCase(
    id="PA_002",
    query="my passport application was rejected or refused by government",
    preferred=("The Passports Act 1967", "6"),
    acceptable=[("The Passports Act 1967", "6")],
    category_filter="administrative",
),

TestCase(
    id="PA_003",
    query="can passport be cancelled or impounded by authorities",
    preferred=("The Passports Act 1967", "10"),
    acceptable=[("The Passports Act 1967", "10")],
    category_filter="administrative",
),

TestCase(
    id="PA_004",
    query="what happens if false information is given in passport application",
    preferred=("The Passports Act 1967", "12"),
    acceptable=[("The Passports Act 1967", "12")],
    category_filter="administrative",
),
]