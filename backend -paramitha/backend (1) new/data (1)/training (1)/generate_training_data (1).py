"""
Script to generate 700+ additional training data entries for CivilModel
following the same JSONL format as existing training_data.jsonl
"""

import json
import random

COURT = "Supreme Court of the Democratic Socialist Republic of Sri Lanka"

# Pool of judges 
JUDGES_POOL = [
    "S. Thurairaja", "Priyantha Jayawardena", "Buwaneka Aluwihare",
    "Mahinda Samayawardhena", "Janak De Silva", "K. Priyantha Fernando",
    "Achala Wengappuli", "Kumudini Wickremasinghe", "Sampath B. Abayakoon",
    "A.L. Shiran Gooneratne", "E.A.G.R. Amarasekara", "Yasantha Kodagoda",
    "P. Padman Surasena", "Arjuna Obeyesekere", "Menaka Wijesundera",
    "Murdu N.B. Fernando", "A.H.M.D. Nawaz", "M. Sampath K. B. Wijeratne",
    "Vijith K. Malalgoda", "Sobhitha Rajakaruna", "K. Kumudini Wickremasinghe",
    "Eva Wanasundera", "Sisira J De Abrew", "Upaly Abeyrathne",
    "Anil Gooneratne", "Chandra Ekanayake", "Rohini Marasinghe",
    "Nalin Perera", "Priyasath Dep", "K. Sripavan",
    "Saleem Marsoof", "Shiranee Tilakawardane", "Dr. Shirani A. Bandaranayake",
    "Mohan Pieris", "L.T.B. Dehideniya", "Sarath de Abrew",
    "Jayantha Jayasuriya", "Sampath K.B. Wijeratne", "R.A.N.G. Amaratunga",
    "Sathyaa Hettige", "P. Dep"
]

SL_NAMES_PLAINTIFFS = [
    "Karunasena Arachchi", "Wasantha Perera", "Nimal Silva",
    "Sunil Jayawardena", "Kamala Fernando", "Dharmasiri Wickramasinghe",
    "Premadasa Bandara", "Rukmini Dissanayake", "Lalith Kumara",
    "Anura Senanayake", "Chandrani Jayasinghe", "Gamini Ranasinghe",
    "Wijayapala Munasinghe", "Thilaka Ratnayake", "Pushpa Amarasinghe",
    "Rohan Gunawardana", "Seetha Wijesekera", "Asoka Liyanage",
    "Sirisena De Silva", "Manel Rajapaksha", "Lakshman Kumaratunga",
    "Pradeep Herath", "Sujatha Pathirana", "Nuwan Samaraweera",
    "Dilrukshi Abeyratne", "Ranjith Dias", "Chaminda Marasinghe",
    "Saroja Kodithuwakku", "Upali Piyadasa", "Samantha Gunasekara",
    "Mohamed Farook", "Fathima Rifka", "Abdul Hameed Ibrahim",
    "Krishnaswamy Kandeepan", "Rasiah Thilagavathi", "Selvakumar Arumugam",
    "Velupillai Nithyanandam", "Tamil Selvan Ramachandran",
    "Don Albert Jayasinghe", "Carmel Pereira", "Francis Fernando",
    "Joseph Peiris", "Peter Jayasekara", "Mary Rodrigo",
    "Somawathie Senaratne", "Mallika Hettiarachchi", "Sumalatha Jayakody",
    "Rangi Weerasinghe", "Wimaladasa Jayarathna", "Kusuma Piyatilaka"
]

SL_NAMES_DEFENDANTS = [
    "Bank of Ceylon", "People's Bank", "Commercial Bank of Ceylon PLC",
    "Hatton National Bank PLC", "Sampath Bank PLC",
    "National Development Bank PLC", "DFCC Bank PLC",
    "Sri Lanka Insurance Corporation", "Ceylinco Insurance PLC",
    "Dialog Axiata PLC", "SriLankan Airlines Limited",
    "Ceylon Electricity Board", "National Water Supply and Drainage Board",
    "Road Development Authority", "Urban Development Authority",
    "Land Reform Commission", "Department of Agrarian Development",
    "Municipal Council Colombo", "Pradeshiya Sabha Gampaha",
    "Wijeya Newspapers Limited", "Lake House Publications",
    "Richard Pieris and Company PLC", "Aitken Spence PLC",
    "John Keells Holdings PLC", "Hemas Holdings PLC",
    "Central Finance Company Limited", "Mercantile Investment PLC",
    "Lanka Tiles Limited", "Dankotuwa Porcelain PLC",
    "Attorney General", "Inspector General of Police",
    "Commissioner General of Lands", "Land Commissioner General",
    "Secretary Ministry of Justice", "Director General Customs",
    "Weerasinghe Mudiyanselage Bandara", "Gunasekara Arachchige Upali",
    "Kaluarachchige Saman Priyantha", "Hewage Dhamma Ratne",
    "Manike Marasinghe", "Podiyapalage Hemantha"
]

# ─────────────────────────────────────────
# SC APPEAL cases – Civil (Partition / Contract / Prescription / Property)
# ─────────────────────────────────────────

def make_sc_appeal_partition(idx):
    year = random.randint(2005, 2023)
    case_num = f"SC Appeal {idx}/{year - random.randint(0, 3)}"
    decided_year = random.randint(year + 1, 2025)
    decided = f"{decided_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    argued_year = decided_year - random.randint(0, 2)
    argued = f"{argued_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    j3 = random.sample(JUDGES_POOL, 3)
    p1 = random.choice(SL_NAMES_PLAINTIFFS)
    p2 = random.choice(SL_NAMES_DEFENDANTS)
    writing_j = j3[2]

    deed_no = random.randint(100, 9999)
    parcel_acres = round(random.uniform(0.5, 5.0), 2)
    
    topics = [
        (
            f"partition action re land parcel {parcel_acres} acres; Deed No. {deed_no}; prescriptive title dispute under Section 3 Prescription Ordinance",
            f"Prescription Ordinance sections 3 and 7; ten-year possession requirements; documentary evidence of deeds and survey plans; witnesses on continuous undisturbed possession; adverse possession principles",
            f"Appeal dismissed; District Court and High Court judgments affirmed; prescriptive title established; appeal dismissed"
        ),
        (
            f"partition action; plaint filed under Partition Law; respondent challenges surveyor's plan; dispute over identification of corpus",
            f"Partition Law sections 18 and 25; surveyor's duty to identify corpus; Section 18(1)(a)(iii) requirements; reconciliation of plan discrepancies with deed descriptions",
            f"Appeal allowed; High Court order set aside; District Court judgment restored; corpus correctly identified in survey plan"
        ),
        (
            f"partition action; co-owners dispute over share entitlements; Deed of Gift No. {deed_no-10} challenged for lack of capacity",
            f"Deed of Gift validity; donor capacity at time of execution; notarial attestation requirements; Deeds Ordinance section 2; evidence of mental incapacity; medical expert testimony",
            f"Appeal dismissed; partition decree upheld; Deed of Gift valid; shares allotted per plan confirmed; no costs"
        ),
        (
            f"long-running partition action; substitution of deceased plaintiff; litis contestatio and purge-default issues",
            f"Sections 337 and 398 CPC on substitution; litis contestatio effect; whether substituted plaintiff inherits default; distinction between mere procedural default and substantive failure",
            f"Appeal partly allowed; substituted plaintiff entitled to purge default; case remitted for further inquiry; costs awarded to appellant"
        ),
        (
            f"partition action; objection to preliminary plan under Partition Law; extent discrepancy between plan and deed schedule",
            f"Partition Law section 18(1)(a)(iii); surveyor report analysis; reasonable discrepancy in extent; Court of Appeal erred in dismissing action; principle that plan need only substantially identify corpus",
            f"Appeal allowed; Civil Appellate High Court judgment set aside; District Court partition decree restored; no costs"
        )
    ]
    topic_data = random.choice(topics)
    header_extra, analysis_extra, conclusion = topic_data

    return {
        "metadata": {
            "case_number": case_num,
            "court": COURT,
            "date": decided,
            "parties": [p1] + random.sample(SL_NAMES_DEFENDANTS, random.randint(1, 3)),
            "judges": j3
        },
        "sections": [
            {
                "title": "Header and Case Details",
                "content": f"IN THE SUPREME COURT...{case_num}; {p1} v {p2}; {header_extra}; Before: {j3[0]} J, {j3[1]} J, {j3[2]} J; Argued {argued}; Decided {decided}."
            },
            {
                "title": "Judgment and Legal Analysis",
                "content": f"{writing_j}, J: {analysis_extra}; review of District Court and High Court findings; appellate principles on interference with findings of fact; evidence assessed."
            },
            {
                "title": "Conclusion and Order",
                "content": f"Conclusion: {conclusion}. Decided on {decided}."
            }
        ]
    }


def make_sc_appeal_contract(idx):
    year = random.randint(2005, 2023)
    case_num = f"SC Appeal {idx}/{year - random.randint(0, 3)}"
    decided_year = random.randint(year + 1, 2025)
    decided = f"{decided_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    argued_year = decided_year - random.randint(0, 2)
    argued = f"{argued_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    j3 = random.sample(JUDGES_POOL, 3)
    p1 = random.choice(SL_NAMES_PLAINTIFFS)
    p2 = random.choice(SL_NAMES_DEFENDANTS)
    writing_j = j3[2]

    amount = random.randint(500000, 50000000)

    contract_types = [
        (
            "agreement of sale; specific performance; vendor failed to execute transfer deed",
            f"specific performance principles under Roman-Dutch law; readiness and willingness of purchaser to pay balance (Rs.{amount:,}); vendor's deliberate refusal; whether damages adequate remedy; equitable considerations",
            f"Appeal allowed; specific performance ordered; vendor directed to execute transfer deed within 30 days; appeal allowed with costs Rs.50,000"
        ),
        (
            "breach of contract; sale of goods; delivery notes and invoices disputed; one-year prescription under Prescription Ordinance section 7",
            f"Prescription Ordinance section 7 (one-year limitation for sale of goods); whether P7 acknowledgement takes action out of limitation under section 8; evidentiary value of delivery notes proved under section 67 Evidence Ordinance",
            f"Appeal dismissed; prescription period not expired; acknowledgement valid; High Court judgment affirmed; no costs"
        ),
        (
            "construction contract; measure-and-pay vs. lump-sum; extra work claims",
            f"interpretation of construction contract terms; whether oral authorization sufficient for extras; valuation of work done; Civil Procedure Code section 12 on certified claims; principle that extraordinary claims require stronger evidence",
            f"Appeal partly allowed; extra work claims reduced; lump-sum contract terms prevail; contractor entitled to balance only on agreed scope"
        ),
        (
            "employment contract; wrongful termination; reinstatement vs. compensation",
            f"Industrial Disputes Act applicability; wrongful termination without cause; employee's entitlement to reinstatement; whether long-gap precludes reinstatement; back-wages calculation",
            f"Appeal dismissed; High Court order for compensation affirmed; reinstatement impractical after {random.randint(5,15)} years; back-wages calculated at {random.randint(50, 100)}%"
        ),
        (
            "guarantee and indemnity; surety liability; whether bank demand letter proper",
            f"Contract Law on guarantee vs. indemnity; co-extensive liability of guarantor; demand requirements under guarantee deed; evidence of principal debtor default; limitation period for sureties",
            f"Appeal dismissed; guarantor liable; demand requirements satisfied; bank entitled to recover Rs.{amount:,} from surety; appeal dismissed with costs"
        )
    ]
    topic_data = random.choice(contract_types)
    header_extra, analysis_extra, conclusion = topic_data

    return {
        "metadata": {
            "case_number": case_num,
            "court": COURT,
            "date": decided,
            "parties": [p1, p2],
            "judges": j3
        },
        "sections": [
            {
                "title": "Header and Case Details",
                "content": f"IN THE SUPREME COURT...{case_num}; {p1} v {p2}; {header_extra}; Before: {j3[0]} J, {j3[1]} J, {j3[2]} J; Argued {argued}; Decided {decided}."
            },
            {
                "title": "Judgment and Legal Analysis",
                "content": f"{writing_j}, J: {analysis_extra}; evidence from District Court and High Court reviewed; questions of law answered."
            },
            {
                "title": "Conclusion and Order",
                "content": f"Conclusion: {conclusion}. Decided on {decided}."
            }
        ]
    }


def make_sc_appeal_family(idx):
    year = random.randint(2006, 2022)
    case_num = f"SC Appeal {idx}/{year - random.randint(0, 4)}"
    decided_year = random.randint(year + 2, 2025)
    decided = f"{decided_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    argued_year = decided_year - random.randint(0, 2)
    argued = f"{argued_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    j3 = random.sample(JUDGES_POOL, 3)
    p1 = random.choice(SL_NAMES_PLAINTIFFS)
    p2 = random.choice(SL_NAMES_PLAINTIFFS)
    writing_j = j3[0]

    family_topics = [
        (
            "divorce petition; malicious desertion; General Marriage Ordinance",
            "General Marriage Ordinance section 19(1)(c); malicious desertion definition; factum of separation plus animus deserendi; Bipinchandra Shah principles; whether respondent justified in leaving matrimonial home; cross-examination credibility",
            "Appeal dismissed; malicious desertion proved; divorce granted; High Court judgment affirmed"
        ),
        (
            "maintenance application; wife and children; quantum of maintenance order",
            "Maintenance Ordinance; financial capacity of respondent; children's educational needs; standard of living before separation; assessment of income from business and property",
            f"Appeal partly allowed; maintenance increased to Rs.{random.randint(10000, 100000):,} per month; order varied to current financial circumstances"
        ),
        (
            "custody dispute; child's best interests; Guardianship and Custody Order",
            "Children and Young Persons Ordinance; paramount consideration of child's welfare; attachment and bonding assessment; schooling continuity; whether change of custody serves best interests",
            "Appeal dismissed; custody with mother affirmed; father granted reasonable access; welfare report accepted"
        ),
        (
            "Kandyan marriage; nindagam property; inheritance rights under Kandyan law",
            "application of Kandyan Law Ordinance; nindagam property definition; joint family property rights; whether conversion terminates Kandyan law applicability; succession under Kandyan custom vs. general law",
            "Appeal partly allowed; nindagam property rights recognized; division ordered per Kandyan Law proportions"
        ),
        (
            "testamentary capacity; will challenge; undue influence claim",
            "Testamentary capacity requirements under Roman-Dutch law; sound disposing mind; undue influence elements (susceptibility, opportunity, exerted influence, resulting will); medical evidence assessed; witness credibility",
            "Appeal dismissed; will valid; testamentary capacity established; undue influence claim not proved on balance of probabilities"
        )
    ]
    topic_data = random.choice(family_topics)
    header_extra, analysis_extra, conclusion = topic_data

    return {
        "metadata": {
            "case_number": case_num,
            "court": COURT,
            "date": decided,
            "parties": [p1, p2],
            "judges": j3
        },
        "sections": [
            {
                "title": "Header and Case Details",
                "content": f"IN THE SUPREME COURT...{case_num}; {p1} v {p2}; {header_extra}; Before: {j3[0]} J, {j3[1]} J, {j3[2]} J; Argued {argued}; Decided {decided}."
            },
            {
                "title": "Judgment and Legal Analysis",
                "content": f"{writing_j}, J: {analysis_extra}; evidence weighed; prior High Court findings reviewed."
            },
            {
                "title": "Conclusion and Order",
                "content": f"Conclusion: {conclusion}. Decided on {decided}."
            }
        ]
    }


# ─────────────────────────────────────────
# SC FR cases – Fundamental Rights
# ─────────────────────────────────────────

def make_sc_fr(idx):
    year = random.randint(2008, 2023)
    case_num = f"SC FR {idx}/{year}"
    decided_year = random.randint(year + 1, 2025)
    decided = f"{decided_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    argued_year = decided_year - random.randint(0, 2)
    argued = f"{argued_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    j3 = random.sample(JUDGES_POOL, 3)
    p1 = random.choice(SL_NAMES_PLAINTIFFS)
    writing_j = j3[1]

    amount = random.randint(50000, 500000)

    fr_topics = [
        (
            "alleged police assault in custody; Articles 11, 13(1) violation",
            "Article 11 (freedom from torture/degrading treatment - absolute right); Article 13(1) (due process of arrest); Sudath Silva v Kodituakku standard; medical evidence MLR; credibility of petitioner vs. police affidavit; corroboration requirements",
            f"Petition allowed; Article 11 violated; declaration granted; respondents ordered to pay Rs.{amount:,} compensation from personal funds; criminal investigation directed",
            True
        ),
        (
            "arbitrary arrest; detention without production before magistrate within 24 hours; Article 13(2) violation",
            f"Article 13(2) Constitution (production before magistrate within 24 hours); CPC Schedule 1 offences; lawfulness of arrest without warrant; period of detention {random.randint(36, 72)} hours before magistrate production; evidence of unconstitutional delay",
            f"Petition allowed; Articles 13(1) and 13(2) violated; declaration granted; compensation Rs.{amount:,}; Inspector General directed to investigate",
            True
        ),
        (
            "right to livelihood; demolition of business premises without due process; Article 14(1)(g) violation",
            "Article 14(1)(g) (right to engage in lawful occupation); whether demolition order followed proper procedure; Urban Development Authority Act requirements; legitimate expectation doctrine; proportionality analysis",
            f"Petition partly allowed; Article 14(1)(g) violated; demolition halted pending proper notice; compensation Rs.{amount//2:,} for losses",
            True
        ),
        (
            "employment discrimination; public servant dismissed without inquiry; Article 12(2) violation",
            "Article 12(2) (non-discrimination based on race, religion, language, caste, sex); whether dismissal motivated by protected characteristics; Administrative Appeals Tribunal Act; due process in public employment; natural justice principles",
            f"Petition dismissed; dismissal based on proven misconduct, not discriminatory grounds; petitioner failed to establish prima facie case of discrimination",
            False
        ),
        (
            "freedom of expression; journalist arrested for publication; Article 14(1)(a) violation",
            "Article 14(1)(a) (freedom of speech and expression); Press Council Act limitations; whether publication falls within constitutionally protected expression; Defamation Ordinance offences; balancing individual rights against public order concerns",
            f"Petition allowed; arrest disproportionate; Article 14(1)(a) violated; declaratory relief granted; compensation Rs.{amount:,}",
            True
        ),
        (
            "right to education; exclusion from university admission; Article 12(1) violation",
            "Article 12(1) (equality before law); University Grants Commission Act; Z-score calculation methodology; transparency of admission process; legitimate expectation; whether error discriminatory or purely administrative",
            f"Petition dismissed; no Article 12(1) violation; admission process followed UGC guidelines; petitioner's Z-score correctly calculated",
            False
        ),
        (
            "tender award challenged; public procurement irregularity; Articles 12(1), 14(1)(g) violation",
            "Procurement Guidelines compliance; Articles 12(1) and 14(1)(g) Constitution; lowest compliant tender evaluation; whether rejection of petitioner's bid arbitrary; assessment of technical evaluation committee's methodology",
            f"Petition dismissed; tender evaluation followed National Procurement Guidelines; no arbitrary action; procurement decision valid",
            False
        ),
        (
            "illegal search and seizure; home searched without warrant; Article 13(1) violation",
            "Article 13(1) (protection against arbitrary arrest/search); CPC Section 117 requirements for search warrants; whether emergency exception applies; evidence gathered through illegal search inadmissibility per Section 24 Evidence Ordinance",
            f"Petition allowed; warrantless search violated Article 13(1); declaration granted; compensation Rs.{amount//2:,}; evidence inadmissibility noted",
            True
        ),
        (
            "prison conditions; inadequate medical treatment for remand prisoner; Article 11 violation",
            "Article 11 (right to dignity); Prison Ordinance obligations; standard of care owed to remand prisoners; whether failure to provide adequate medical treatment constitutes degrading treatment; Nelson Perera principles",
            f"Petition partly allowed; inadequate medical care violated Article 11; prison medical facilities directed to improve; nominal compensation Rs.50,000 awarded",
            True
        ),
        (
            "transfer of public officer; punitive transfer without valid ground; Article 12(1) violation",
            "Article 12(1) (equality before law); Public Administration Circular provisions; whether transfer made in bad faith; burden on petitioner to establish mala fides; legitimate expectation of fair treatment in transfer decisions",
            f"Petition dismissed; transfer within employer's discretion; no mala fides established; petitioner failed to discharge burden of proof",
            False
        )
    ]

    topic_data = random.choice(fr_topics)
    header_extra, analysis_extra, conclusion, allowed = topic_data

    return {
        "metadata": {
            "case_number": case_num,
            "court": COURT,
            "date": decided,
            "parties": [p1, "Attorney General", "Inspector General of Police"],
            "judges": j3
        },
        "sections": [
            {
                "title": "Header and Case Details",
                "content": f"IN THE SUPREME COURT...{case_num}; {p1} v Attorney General and others; fundamental rights application; {header_extra}; Before: {j3[0]} J, {j3[1]} J, {j3[2]} J; Argued {argued}; Decided {decided}."
            },
            {
                "title": "Judgment and Legal Analysis",
                "content": f"{writing_j}, J: {analysis_extra}; evidence and affidavits assessed; respondents' position examined; balancing of competing interests."
            },
            {
                "title": "Conclusion and Order",
                "content": f"Conclusion: {conclusion}. Decided on {decided}."
            }
        ]
    }


# ─────────────────────────────────────────
# SC CHC Appeal – Commercial High Court
# ─────────────────────────────────────────

def make_sc_chc(idx):
    year = random.randint(2003, 2021)
    case_num = f"SC CHC Appeal {idx}/{year}"
    decided_year = random.randint(year + 1, 2025)
    decided = f"{decided_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    argued_year = decided_year - random.randint(0, 2)
    argued = f"{argued_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    j3 = random.sample(JUDGES_POOL, 3)
    p1 = random.choice(SL_NAMES_PLAINTIFFS + ["ABC Trading (Pvt) Ltd", "XYZ Enterprises (Pvt) Ltd",
                                               "Island Imports (Pvt) Ltd", "Lanka Export Corporation"])
    p2 = random.choice(SL_NAMES_DEFENDANTS)
    writing_j = random.choice(j3)

    amount = random.randint(1000000, 200000000)

    chc_topics = [
        (
            f"commercial dispute; goods sold and delivered; Rs.{amount:,} unpaid invoices",
            f"sale of goods; proof of delivery under Section 67 Evidence Ordinance; acknowledgement of liability (letter P{random.randint(3,12)}); whether defendant discharged liability through third party arrangement; consideration of contra proferentem rule",
            f"Appeal dismissed; Commercial High Court judgment affirmed; plaintiff established delivery and non-payment; defendant liable for Rs.{amount:,}"
        ),
        (
            "banking dispute; recovery of loan; parate execution under Recovery of Loans by Banks Act",
            "Recovery of Loans by Banks Act sections 4 and 5; validity of parate execution; whether bank exercised rights properly; interim injunction criteria (prima facie case, balance of convenience); bank's right to consolidate multiple accounts",
            f"Appeal allowed; interim injunction restraining parate execution set aside; bank entitled to exercise statutory rights; no suppression of material facts by bank"
        ),
        (
            "trade mark infringement; passing off; competing products in similar market",
            "Intellectual Property Act 2003 sections 160 and 142; passing off requirements (goodwill, misrepresentation, damage); visual and phonetic similarity assessment; survey evidence; likelihood of confusion among average consumers",
            f"Appeal dismissed; passing off established; defendant's mark confusingly similar; injunction restraining use of infringing mark upheld; damages Rs.{amount//10:,}"
        ),
        (
            "insurance dispute; rejection of claim; condition precedent not complied with",
            "insurance contract interpretation; condition precedent vs. condition subsequent; notification requirements; prejudice to insurer from late notification; contra proferentem rule applied to ambiguous exclusion clauses; utmost good faith principle",
            f"Appeal partly allowed; insurer not entitled to repudiate claim on technicality; condition construed as warranty not condition precedent; plaintiff recovers Rs.{amount:,}"
        ),
        (
            "ex parte judgment; application to vacate under Section 86(2) CPC; reasonable grounds for default",
            "Section 86(2) CPC (application to vacate ex parte judgment); 'reasonable grounds' standard; distinction between mistake and negligence; delay in filing application; merits of proposed defence; balance of justice",
            "Appeal allowed; reasonable grounds established for default; ex parte judgment vacated; defendant permitted to file answer on payment of Rs.150,000 costs"
        ),
        (
            "breach of insurance policy; fire damage claim; arson allegation against insured",
            "burden of proof in arson allegation (criminal standard vs. civil balance of probabilities); circumstantial evidence; expert fire investigation reports; insured's conduct before and after fire; policy exclusion for deliberate destruction",
            f"Appeal dismissed; insurer failed to prove arson on balance of probabilities; insured's claim valid; insurer ordered to pay Rs.{amount:,} with interest"
        ),
        (
            "copyright infringement; unauthorized reproduction of software; Intellectual Property Act",
            "Intellectual Property Act 2003 Part III (copyright); software as literary work; subsistence of copyright; acts restricted by copyright; whether licence implied; quantification of damages for flagrant infringement",
            f"Appeal dismissed; copyright infringement established; damages Rs.{amount//5:,}; injunction restraining further copying confirmed"
        ),
        (
            "company winding up application; just and equitable ground; shareholder dispute",
            "Companies Act No. 7 of 2007; winding up on just and equitable ground; quasi-partnership principles; legitimate expectations of shareholders; alternative remedies; Court's discretion in winding up vs. buy-out order",
            "Appeal dismissed; winding up ordered being just and equitable; respondent's conduct destroyed mutual trust; buy-out order inappropriate on facts"
        ),
        (
            "arbitration award; enforcement; public policy exception",
            "Arbitration Act No. 11 of 1995; enforcement of foreign arbitration award; public policy grounds for refusal; principle that public policy exception narrowly construed; natural justice compliance in arbitration proceedings",
            f"Appeal dismissed; arbitration award enforced; no violation of public policy; award for Rs.{amount:,} made enforceable"
        ),
        (
            "letter of credit; fraud exception; injunction restraining payment",
            "international letter of credit principles; autonomy principle; fraud exception (clear evidence of fraud); materials fraud at call stage; bank's duty to pay under documentary credits; injunction standard for LC disputes",
            f"Appeal dismissed; fraud not clearly established; bank directed to make payment under LC; injunction restraining payment discharged; autonomy principle upheld"
        )
    ]

    topic_data = random.choice(chc_topics)
    header_extra, analysis_extra, conclusion = topic_data

    return {
        "metadata": {
            "case_number": case_num,
            "court": COURT,
            "date": decided,
            "parties": [p1, p2],
            "judges": j3
        },
        "sections": [
            {
                "title": "Header and Case Details",
                "content": f"IN THE SUPREME COURT...{case_num}; {p1} v {p2}; {header_extra}; Before: {j3[0]} J, {j3[1]} J, {j3[2]} J; Argued {argued}; Decided {decided}."
            },
            {
                "title": "Judgment and Legal Analysis",
                "content": f"{writing_j}, J: {analysis_extra}; Commercial High Court judgment reviewed on appeal; questions of law examined."
            },
            {
                "title": "Conclusion and Order",
                "content": f"Conclusion: {conclusion}. Decided on {decided}."
            }
        ]
    }


# ─────────────────────────────────────────
# SC Appeal – Labour / Administrative / Tort
# ─────────────────────────────────────────

def make_sc_appeal_labour_tort(idx):
    year = random.randint(2007, 2022)
    case_num = f"SC Appeal {idx}/{year - random.randint(0, 3)}"
    decided_year = random.randint(year + 1, 2025)
    decided = f"{decided_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    argued_year = decided_year - random.randint(0, 2)
    argued = f"{argued_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    j3 = random.sample(JUDGES_POOL, 3)
    p1 = random.choice(SL_NAMES_PLAINTIFFS)
    p2 = random.choice(SL_NAMES_DEFENDANTS)
    writing_j = j3[2]

    amount = random.randint(200000, 10000000)

    topics = [
        (
            "motor vehicle accident; negligence; contributory negligence; quantum of damages",
            f"Motor Traffic Act; negligence standard of care; contributory negligence assessment; principles of res ipsa loquitur; general and special damages calculation; future loss of earnings; pain and suffering at Rs.{amount:,}; pre-trial interest",
            f"Appeal partly allowed; contributory negligence assessed at {random.randint(10, 40)}%; total damages reduced proportionally; appeal partly succeeded"
        ),
        (
            "wrongful dismissal; Industrial Disputes Act; reinstatement claim",
            "Industrial Disputes Act No. 43 of 1950; whether employee given opportunity to be heard before dismissal; natural justice in employment; standard of proof for misconduct; long service and reinstatement vs. terminal compensation",
            f"Appeal dismissed; wrongful dismissal upheld; reinstatement ordered with back-wages for {random.randint(1, 10)} years less appropriate deductions"
        ),
        (
            "defamation action; publication in newspaper; qualified privilege",
            "law of defamation; elements of defamation (false statement, publication, damage to reputation); defence of qualified privilege; malice destroying privilege; whether publication in public interest; quantum of general damages",
            f"Appeal dismissed; defamation proved; qualified privilege not available (malice proved); damages Rs.{amount//5:,} affirmed"
        ),
        (
            "nuisance; factory noise/fumes; injunction; damages",
            "private nuisance elements; unreasonable interference with use and enjoyment of neighbour's land; locality principle; duration and nature of interference; available defences (statutory authority, prescription); mandatory injunction to abate nuisance",
            f"Appeal allowed in part; injunction granted restraining operation after 10 PM; damages Rs.{amount//10:,} for past interference; factory subject to conditions"
        ),
        (
            "workmen's compensation; occupational disease; Employment of Women, Young Persons and Children Act",
            "Workmen's Compensation Ordinance; occupational disease schedule; causal link between employment and disease; medical evidence; employer liability; quantum assessment based on degree of incapacity and earnings",
            f"Appeal dismissed; occupational disease causation established; employer liable for compensation Rs.{amount//3:,}; appeal dismissed with costs"
        )
    ]

    topic_data = random.choice(topics)
    header_extra, analysis_extra, conclusion = topic_data

    return {
        "metadata": {
            "case_number": case_num,
            "court": COURT,
            "date": decided,
            "parties": [p1, p2],
            "judges": j3
        },
        "sections": [
            {
                "title": "Header and Case Details",
                "content": f"IN THE SUPREME COURT...{case_num}; {p1} v {p2}; {header_extra}; Before: {j3[0]} J, {j3[1]} J, {j3[2]} J; Argued {argued}; Decided {decided}."
            },
            {
                "title": "Judgment and Legal Analysis",
                "content": f"{writing_j}, J: {analysis_extra}; evidence from trial and appellate courts reviewed; applicable legal principles applied."
            },
            {
                "title": "Conclusion and Order",
                "content": f"Conclusion: {conclusion}. Decided on {decided}."
            }
        ]
    }


# ─────────────────────────────────────────
# SC Writ / Revision Applications
# ─────────────────────────────────────────

def make_sc_writ_revision(idx):
    year = random.randint(2009, 2022)
    app_types = ["SC/Writ", "SC/Rev", "SC(Spl)/LA", "SC/SPL/LA"]
    app_type = random.choice(app_types)
    case_num = f"{app_type}/{idx}/{year}"
    decided_year = random.randint(year + 1, 2025)
    decided = f"{decided_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    argued_year = decided_year - random.randint(0, 2)
    argued = f"{argued_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    j3 = random.sample(JUDGES_POOL, 3)
    p1 = random.choice(SL_NAMES_PLAINTIFFS)
    p2 = random.choice(SL_NAMES_DEFENDANTS)
    writing_j = j3[1]

    topics = [
        (
            "revision application against Court of Appeal order refusing leave to appeal",
            "revisionary jurisdiction; Section 65A Judicature Act; whether Court of Appeal misdirected itself; manifest injustice threshold; limited scope of revision when leave properly refused",
            "Revision application dismissed; Court of Appeal correctly refused leave; no manifest injustice; applicant cannot re-agitate findings of fact through revision"
        ),
        (
            "writ of certiorari; administrative decision of Board of Review; procedural fairness",
            "administrative law; writ of certiorari grounds (jurisdictional error, error of law on face of record, breach of natural justice); Board of Review decision validity; procedural fairness requirements; hearing rights",
            "Writ application allowed; Board of Review order quashed; matter remitted for re-hearing in accordance with natural justice principles"
        ),
        (
            "writ of mandamus; refusal to issue building permit; Urban Development Authority",
            "writ of mandamus; public duty to consider application; Urban Development Authority Act; whether refusal arbitrary; legitimate expectation based on prior approvals; relevant and irrelevant considerations test",
            "Writ application partly allowed; UDA directed to reconsider application on proper legal grounds; no mandamus directing specific outcome"
        ),
        (
            "revision; interlocutory order allowing amendment to plaint; prejudice to defendant",
            "Section 93 CPC amendment powers; whether amendment introduces new cause of action; limitation period implications of amendment; prejudice to defendant; applicability of Courts of Appeal Rules on revision",
            "Revision refused; amendment order correct; no prejudice to defendant not remediable by costs; plaint amendment within court's discretion"
        ),
        (
            "leave to appeal from Court of Appeal; questions of law of public and general importance",
            "Section 5(2) Supreme Court of Appeal Procedure Act; 'public and general importance' threshold; whether arguable point of law warranting leave; distinction between pure factual appellate review and legal question",
            "Leave to appeal refused; questions raised are pure findings of fact; Court of Appeal not misdirected; no public importance threshold met"
        )
    ]

    topic_data = random.choice(topics)
    header_extra, analysis_extra, conclusion = topic_data

    return {
        "metadata": {
            "case_number": case_num,
            "court": COURT,
            "date": decided,
            "parties": [p1, p2],
            "judges": j3
        },
        "sections": [
            {
                "title": "Header and Case Details",
                "content": f"IN THE SUPREME COURT...{case_num}; {p1} v {p2}; {header_extra}; Before: {j3[0]} J, {j3[1]} J, {j3[2]} J; Argued {argued}; Decided {decided}."
            },
            {
                "title": "Judgment and Legal Analysis",
                "content": f"{writing_j}, J: {analysis_extra}; jurisdiction of Supreme Court reviewed; applicable legal tests applied."
            },
            {
                "title": "Conclusion and Order",
                "content": f"Conclusion: {conclusion}. Decided on {decided}."
            }
        ]
    }


# ─────────────────────────────────────────
# Primary Courts Procedure Act / Magistrate's Court cases
# ─────────────────────────────────────────

def make_sc_pcpa(idx):
    year = random.randint(2010, 2022)
    case_num = f"SC Appeal {idx}/{year - random.randint(0, 4)}"
    decided_year = random.randint(year + 1, 2025)
    decided = f"{decided_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    argued_year = decided_year - random.randint(0, 2)
    argued = f"{argued_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    j3 = random.sample(JUDGES_POOL, 3)
    p1 = random.choice(SL_NAMES_PLAINTIFFS)
    p2 = random.choice(SL_NAMES_PLAINTIFFS)
    writing_j = j3[0]

    topics = [
        (
            "Primary Courts Procedure Act section 66; breach of peace; possession of land",
            "PCPA section 66 application; police complaint requirement; sufficiency of evidence for primary court order; distinction between title and possession; assessment of documentary evidence (assessment extracts, electricity bills); appellate scope in PCPA proceedings",
            "Appeal dismissed; Primary Court and High Court findings affirmed; possession correctly determined; respondent in possession entitled to protection from breach of peace"
        ),
        (
            "PCPA section 66; disputed boundary; survey required",
            "PCPA section 66 jurisdiction limits; whether disputed boundary requires survey evidence; capacity of Primary Court to determine boundary disputes; referral for survey under PCPA; distinction from title determination",
            "Appeal allowed; Primary Court order set aside; matter remitted for survey evidence before further order; boundary dispute requires expert evidence"
        ),
        (
            "Magistrate's Court; domestic violence protection order; Prevention of Domestic Violence Act",
            "Prevention of Domestic Violence Act No. 34 of 2005; application for protection order; standard of proof; interim vs. final protection orders; definition of 'domestic relationship'; enforcement mechanisms",
            "Appeal dismissed; protection order properly issued; domestic violence established on evidence; respondent prohibited from contacting petitioner or children"
        )
    ]

    topic_data = random.choice(topics)
    header_extra, analysis_extra, conclusion = topic_data

    return {
        "metadata": {
            "case_number": case_num,
            "court": COURT,
            "date": decided,
            "parties": [p1, p2],
            "judges": j3
        },
        "sections": [
            {
                "title": "Header and Case Details",
                "content": f"IN THE SUPREME COURT...{case_num}; {p1} v {p2}; {header_extra}; Before: {j3[0]} J, {j3[1]} J, {j3[2]} J; Argued {argued}; Decided {decided}."
            },
            {
                "title": "Judgment and Legal Analysis",
                "content": f"{writing_j}, J: {analysis_extra}; review of lower court proceedings; legal questions answered."
            },
            {
                "title": "Conclusion and Order",
                "content": f"Conclusion: {conclusion}. Decided on {decided}."
            }
        ]
    }


# ─────────────────────────────────────────
# Election petitions / Public law
# ─────────────────────────────────────────

def make_sc_election_public(idx):
    year = random.randint(2005, 2022)
    case_types = ["SC/El Pet", "SC/Determination", "SC (SD)"]
    case_type = random.choice(case_types)
    case_num = f"{case_type}/{idx}/{year}"
    decided_year = random.randint(year + 1, 2025)
    decided = f"{decided_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    argued_year = decided_year - random.randint(0, 2)
    argued = f"{argued_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    j3 = random.sample(JUDGES_POOL, 3)
    p1 = random.choice(SL_NAMES_PLAINTIFFS)
    p2 = "Election Commission of Sri Lanka"
    writing_j = j3[0]

    topics = [
        (
            "election petition; corrupt practices; undue influence; Parliamentary Elections Act",
            "Parliamentary Elections Act section 88; corrupt practices definition; undue influence elements; whether money distribution amounts to bribery; evidence of systematic distribution; standard of proof in election petitions (higher than balance of probabilities)",
            "Election petition dismissed; corrupt practices not proved to required standard; no systematic bribery established; election result stands"
        ),
        (
            "constitutional determination; proposed legislation; consistency with Constitution Articles",
            "Article 120 Constitution (reference of Bills); judicial review of proposed legislation before enactment; consistency with fundamental rights chapter; proper scope of pre-enactment review; recommendations to Parliament",
            "Bill determined to be inconsistent with Articles 12(1) and 14(1)(a) Constitution; requires two-thirds majority; Parliament to be informed accordingly"
        ),
        (
            "election petition; disqualification of candidate; eligibility requirements",
            "Parliamentary Elections Act; candidate eligibility under Article 91 Constitution; disqualification grounds; citizenship requirements; dual citizenship prohibition; whether disqualification established on evidence",
            "Election petition allowed; returned candidate declared disqualified; election result void; by-election to be held per Elections Commission direction"
        )
    ]

    topic_data = random.choice(topics)
    header_extra, analysis_extra, conclusion = topic_data

    return {
        "metadata": {
            "case_number": case_num,
            "court": COURT,
            "date": decided,
            "parties": [p1, p2],
            "judges": j3
        },
        "sections": [
            {
                "title": "Header and Case Details",
                "content": f"IN THE SUPREME COURT...{case_num}; {p1} v {p2}; {header_extra}; Before: {j3[0]} J, {j3[1]} J, {j3[2]} J; Argued {argued}; Decided {decided}."
            },
            {
                "title": "Judgment and Legal Analysis",
                "content": f"{writing_j}, J: {analysis_extra}; constitutional analysis conducted; precedents reviewed."
            },
            {
                "title": "Conclusion and Order",
                "content": f"Conclusion: {conclusion}. Decided on {decided}."
            }
        ]
    }


# ─────────────────────────────────────────
# MAIN GENERATION
# ─────────────────────────────────────────

def generate_all(target=750):
    """Generate `target` entries across all case types."""
    entries = []
    
    generators = [
        (make_sc_appeal_partition, 0.18),
        (make_sc_appeal_contract, 0.18),
        (make_sc_appeal_family, 0.10),
        (make_sc_fr, 0.22),
        (make_sc_chc, 0.16),
        (make_sc_appeal_labour_tort, 0.08),
        (make_sc_writ_revision, 0.04),
        (make_sc_pcpa, 0.02),
        (make_sc_election_public, 0.02),
    ]

    # Normalise weights
    funcs = [g[0] for g in generators]
    weights = [g[1] for g in generators]

    idx_counters = {f.__name__: random.randint(1, 20) for f in funcs}

    for i in range(target):
        gen_func = random.choices(funcs, weights=weights, k=1)[0]
        name = gen_func.__name__
        idx_counters[name] += random.randint(1, 5)
        entry = gen_func(idx_counters[name])
        entries.append(entry)

    return entries


if __name__ == "__main__":
    import os
    output_path = os.path.join(os.path.dirname(__file__), "training_data.jsonl")
    
    entries = generate_all(750)
    
    with open(output_path, "a", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"Successfully appended {len(entries)} entries to {output_path}")
    
    # Count total lines
    with open(output_path, "r", encoding="utf-8") as f:
        total = sum(1 for line in f if line.strip())
    print(f"Total entries in file: {total}")
