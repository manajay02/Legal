import json
import os
import re
from src.inference.predict import predict


# ==============================
# Load statutory rules
# ==============================
def load_statutes():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(base_dir, "data", "statutes_structured", "statutes.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ==============================
# CLAUSE CATEGORY TO LAW MAPPING
# ==============================
CATEGORY_LAW_MAPPING = {
    # ========== EMPLOYMENT DOMAIN ==========
    "administrative": {
        "act": "Shop and Office Employees Act",
        "section": "General",
        "rule": "Administrative clauses in employment contracts should comply with employment law."
    },
    "identification": {
        "act": "Shop and Office Employees Act",
        "section": "2",
        "rule": "Parties to an employment contract must be clearly identified."
    },
    "commencement": {
        "act": "Shop and Office Employees Act",
        "section": "2",
        "rule": "Employment commencement date and position details should be specified."
    },
    "place_of_work": {
        "act": "Shop and Office Employees Act",
        "section": "2",
        "rule": "Place of work should be specified in employment contracts."
    },
    "assignment_of_duties": {
        "act": "Shop and Office Employees Act",
        "section": "General",
        "rule": "Assignment of duties should be reasonable and within scope of employment."
    },
    "probation": {
        "act": "Termination of Employment of Workmen Act / Industrial Disputes Act",
        "section": "2(1) / 31B",
        "rule": "Probationary periods are permitted but termination during probation may still be challengeable under Industrial Disputes Act Section 31B if employee is a 'workman'."
    },
    "salary": {
        "act": "Wages Boards Ordinance",
        "section": "17",
        "rule": "Wages must be clearly specified and paid at regular intervals not exceeding one month."
    },
    "minimum_wage": {
        "act": "National Minimum Wage of Workers Act",
        "section": "3",
        "rule": "No employee shall be paid less than the national minimum wage as prescribed."
    },
    "wage_deduction": {
        "act": "Wages Boards Ordinance",
        "section": "18",
        "rule": "Unlawful deductions from wages are prohibited without proper authorization."
    },
    "epf": {
        "act": "Employees' Provident Fund Act",
        "section": "8",
        "rule": "Employer must contribute 12% and employee 8% of earnings to EPF."
    },
    "etf": {
        "act": "Employees' Trust Fund Act",
        "section": "2",
        "rule": "Employer must contribute 3% of employee earnings to ETF."
    },
    "epf_etf": {
        "act": "Employees' Provident Fund Act / Employees' Trust Fund Act",
        "section": "8 / 2",
        "rule": "EPF 12%+8% and ETF 3% contributions are mandatory statutory requirements."
    },
    "gratuity": {
        "act": "Payment of Gratuity Act",
        "section": "2(1)",
        "rule": "Employees with 5+ years of service are entitled to half month's wages per year of service as gratuity."
    },
    "working_hours": {
        "act": "Shop and Office Employees Act",
        "section": "3(1)",
        "rule": "Normal working hours shall not exceed 8 hours per day or 45 hours per week."
    },
    "overtime": {
        "act": "Shop and Office Employees Act",
        "section": "4",
        "rule": "Overtime work requires 1.5x normal wage rate compensation."
    },
    "leave": {
        "act": "Shop and Office Employees Act",
        "section": "6",
        "rule": "Employees are entitled to annual leave (14 days), casual leave (7 days), and sick leave (7 days)."
    },
    "annual_leave": {
        "act": "Shop and Office Employees Act",
        "section": "6(1)",
        "rule": "Employees are entitled to 14 days annual leave per year."
    },
    "maternity": {
        "act": "Maternity Benefits Ordinance",
        "section": "2",
        "rule": "Female employees are entitled to 84 working days paid maternity leave."
    },
    "public_holiday": {
        "act": "Shop and Office Employees Act",
        "section": "7(1)",
        "rule": "Employees must be given paid public holidays or double pay in lieu."
    },
    "termination": {
        "act": "Termination of Employment of Workmen Act",
        "section": "2(1)",
        "rule": "Termination requires valid cause, proper notice, and written reasons within 14 days."
    },
    "termination_notice": {
        "act": "Termination of Employment of Workmen Act",
        "section": "2(4)",
        "rule": "Employer must provide written reasons for termination within 14 days of request."
    },
    "instant_dismissal": {
        "act": "Industrial Disputes Act",
        "section": "31B(1)(c)",
        "rule": "Summary dismissal without investigation or hearing violates natural justice principles."
    },
    "retrenchment": {
        "act": "Termination of Employment of Workmen Act",
        "section": "2(2)",
        "rule": "Retrenchment requires prior written notice to Commissioner of Labour."
    },
    "dispute": {
        "act": "Industrial Disputes Act",
        "section": "31B(1)(a)",
        "rule": "Employees have the right to refer disputes to labour tribunals within 6 months."
    },
    "collective_bargaining": {
        "act": "Industrial Disputes Act",
        "section": "4",
        "rule": "Employees have the right to be represented by trade unions in collective bargaining."
    },
    "young_persons": {
        "act": "Employment of Women, Young Persons and Children Act",
        "section": "13",
        "rule": "Employment of young persons (under 18) is restricted and requires special conditions."
    },
    "night_work": {
        "act": "Employment of Women, Young Persons and Children Act",
        "section": "2",
        "rule": "Night work restrictions apply to young persons and women in certain industries."
    },
    "confidentiality": {
        "act": "Common Law",
        "section": "Contract Law Principles",
        "rule": "Confidentiality obligations are enforceable if reasonable in scope and duration."
    },
    "ip": {
        "act": "Intellectual Property Act No. 36 of 2003",
        "section": "Part II",
        "rule": "Work-for-hire intellectual property typically belongs to the employer under common law principles."
    },
    "non_compete": {
        "act": "Common Law",
        "section": "Restraint of Trade Doctrine",
        "rule": "Non-compete clauses must be reasonable in time, geography, and scope to be enforceable."
    },
    "entire_agreement": {
        "act": "Common Law",
        "section": "Contract Law Principles",
        "rule": "Entire agreement clauses are standard contract provisions."
    },
    "acknowledgment": {
        "act": "Common Law",
        "section": "Contract Law Principles",
        "rule": "Acknowledgment clauses confirm receipt and understanding of terms."
    },
    "general": {
        "act": "Common Law",
        "section": "Contract Law Principles",
        "rule": "Standard contract provisions must comply with general contract law principles."
    },
    
    # ========== RENTAL DOMAIN ==========
    "rent": {
        "act": "Rent Act",
        "section": "3",
        "rule": "Standard rent shall be the rent agreed upon between landlord and tenant."
    },
    "rent_increase": {
        "act": "Rent Act",
        "section": "10",
        "rule": "Rent increases are regulated and cannot exceed prescribed limits without proper procedure."
    },
    "advance_rent": {
        "act": "Rent Act",
        "section": "9(1)(a)",
        "rule": "Advance rent shall not exceed 3 months of standard rent."
    },
    "key_money": {
        "act": "Rent Act",
        "section": "9",
        "rule": "Key money, goodwill, or premium payments exceeding limits are prohibited."
    },
    "tenancy": {
        "act": "Rent Act",
        "section": "2",
        "rule": "Tenancy agreements must comply with the Rent Act provisions and be in writing."
    },
    "lease_registration": {
        "act": "Registration of Documents Ordinance",
        "section": "2",
        "rule": "Leases exceeding 1 year must be registered to be enforceable against third parties."
    },
    "eviction": {
        "act": "Rent Act",
        "section": "22",
        "rule": "Eviction requires court order and valid grounds such as non-payment or breach."
    },
    "eviction_grounds": {
        "act": "Rent Act",
        "section": "22(1)",
        "rule": "Landlord must prove valid grounds under Section 22 to obtain possession."
    },
    "security_deposit": {
        "act": "Rent Act",
        "section": "9",
        "rule": "Security deposits must be specified and refundable at end of tenancy."
    },
    "subletting": {
        "act": "Rent Act",
        "section": "10",
        "rule": "Subletting without landlord consent may be restricted but cannot be absolutely prohibited."
    },
    "maintenance": {
        "act": "Rent Act",
        "section": "16",
        "rule": "Landlord is responsible for structural repairs; tenant for minor day-to-day maintenance."
    },
    "essential_services": {
        "act": "Rent Act",
        "section": "17",
        "rule": "Landlord must provide and maintain essential services like water and electricity."
    },
    "notice_eviction": {
        "act": "Rent Act",
        "section": "22",
        "rule": "Proper notice must be given before eviction proceedings can commence."
    },
    "tenant_rights": {
        "act": "Rent Act",
        "section": "32",
        "rule": "Agreements contracting out of Rent Act protections are void."
    },
    "rent_receipt": {
        "act": "Rent Act",
        "section": "33",
        "rule": "Landlord must provide receipt for rent payments upon tenant's request."
    },
    
    # ========== CONSUMER/LOAN DOMAIN ==========
    "loan": {
        "act": "Money Lending Ordinance",
        "section": "3",
        "rule": "Loan agreements must be in writing and clearly state principal, interest, and terms."
    },
    "interest": {
        "act": "Money Lending Ordinance",
        "section": "10",
        "rule": "Interest rates exceeding legal limits or compound interest clauses may be unenforceable."
    },
    "excessive_interest": {
        "act": "Money Lending Ordinance",
        "section": "10",
        "rule": "Courts may reopen transactions with excessive or unconscionable interest rates."
    },
    "compound_interest": {
        "act": "Money Lending Ordinance",
        "section": "11",
        "rule": "Compound interest on loans is restricted and may be unenforceable."
    },
    "repayment": {
        "act": "Consumer Credit Act",
        "section": "6",
        "rule": "Repayment terms and schedules must be clearly specified in writing."
    },
    "early_settlement": {
        "act": "Consumer Credit Act",
        "section": "9",
        "rule": "Borrowers have the right to early settlement with appropriate rebate on interest."
    },
    "cooling_off": {
        "act": "Consumer Credit Act",
        "section": "5",
        "rule": "Consumer has the right to cancel credit agreement within cooling-off period."
    },
    "disclosure": {
        "act": "Consumer Credit Act",
        "section": "3",
        "rule": "Creditors must disclose all fees, charges, and terms before agreement."
    },
    "sale": {
        "act": "Sale of Goods Ordinance",
        "section": "15",
        "rule": "Goods must be of merchantable quality and fit for purpose."
    },
    "merchantable_quality": {
        "act": "Sale of Goods Ordinance",
        "section": "14",
        "rule": "Goods sold must be of merchantable quality free from defects."
    },
    "fitness_purpose": {
        "act": "Sale of Goods Ordinance",
        "section": "15",
        "rule": "Goods must be reasonably fit for the purpose made known to seller."
    },
    "title": {
        "act": "Sale of Goods Ordinance",
        "section": "13",
        "rule": "Seller must have right to sell and goods must be free from encumbrances."
    },
    "warranty": {
        "act": "Sale of Goods Ordinance",
        "section": "15",
        "rule": "Implied warranties of quality and fitness apply to consumer sales."
    },
    "hire_purchase": {
        "act": "Consumer Credit Act",
        "section": "11",
        "rule": "Hire-purchase agreements must disclose total price and right to terminate."
    },
    "finance_lease": {
        "act": "Finance Leasing Act",
        "section": "3",
        "rule": "Finance lease agreements must be registered and clearly state terms."
    },
    "microfinance": {
        "act": "Microfinance Act",
        "section": "24",
        "rule": "Microfinance institutions must be licensed and follow fair lending practices."
    },
    "unfair_terms": {
        "act": "Unfair Contract Terms Act",
        "section": "2",
        "rule": "Exclusion clauses for negligence causing death or injury are void."
    },
    "consumer_protection": {
        "act": "Consumer Affairs Authority Act",
        "section": "10",
        "rule": "Consumers have protection against unfair trade practices."
    },
    "unfair_trade": {
        "act": "Consumer Affairs Authority Act",
        "section": "18",
        "rule": "Unfair trade practices including false representations are prohibited."
    },
    "product_liability": {
        "act": "Consumer Affairs Authority Act",
        "section": "31",
        "rule": "Suppliers are liable for defective products causing harm to consumers."
    },
    "pawnbroking": {
        "act": "Pawnbrokers Ordinance",
        "section": "15",
        "rule": "Pawnbrokers must provide proper receipt and follow redemption procedures."
    },
    
    # ========== FINANCE LEASING DOMAIN ==========
    "lease_term": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "3",
        "rule": "Finance lease term and commencement date must be clearly specified."
    },
    "lease_rental": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "3",
        "rule": "Lease rental amounts and payment schedule must be clearly specified."
    },
    "lease_payment": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "3",
        "rule": "Payment terms including due dates must be specified in writing."
    },
    "late_payment_charge": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "20",
        "rule": "Late payment charges must be reasonable and clearly disclosed."
    },
    "early_termination": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "20",
        "rule": "Early termination conditions must comply with the Finance Leasing Act."
    },
    "repossession": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "21(1)",
        "rule": "Before enforcing default rights, the lessor must serve written notice specifying the default and timeline to remedy."
    },
    "vehicle_maintenance": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "12",
        "rule": "The lessee must care for and properly use the leased equipment."
    },
    "vehicle_insurance": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "12",
        "rule": "Insurance and care obligations of the lessee."
    },
    "lease_assignment": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "3",
        "rule": "Assignment or transfer of lease rights must comply with the agreement terms."
    },
    "lessor_liability": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "11(1)",
        "rule": "The lessee has a right to peaceful possession; lessor liability exclusions must be reasonable."
    },
    "lease_dispute": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "General",
        "rule": "Dispute resolution clauses must not exclude legal remedies."
    },
    "lease_governing_law": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "General",
        "rule": "Finance leasing agreements in Sri Lanka are governed by the Finance Leasing Act."
    },
    "quiet_possession": {
        "act": "Finance Leasing Act, No. 56 of 2000",
        "section": "11(1)",
        "rule": "A lessee has a right to peaceful possession of leased equipment."
    },
    
    "electronic_contract": {
        "act": "Electronic Transactions Act",
        "section": "4",
        "rule": "Electronic contracts are valid and enforceable under certain conditions."
    },
    "partnership": {
        "act": "Partnership Ordinance",
        "section": "28",
        "rule": "Partners have rights to share in profits and participate in management."
    },

    # ========== SALE OF GOODS DOMAIN ==========
    "sale_goods": {
        "act": "Sale of Goods Ordinance, No. 11 of 1896",
        "section": "13",
        "rule": "Seller must have right to sell and goods must be free from encumbrances."
    },
    "merchantable_quality": {
        "act": "Sale of Goods Ordinance, No. 11 of 1896",
        "section": "14",
        "rule": "Goods sold must be of merchantable quality free from defects."
    },
    "fitness_purpose": {
        "act": "Sale of Goods Ordinance, No. 11 of 1896",
        "section": "15",
        "rule": "Goods must be reasonably fit for the purpose made known to seller."
    },
    "sale_delivery": {
        "act": "Sale of Goods Ordinance, No. 11 of 1896",
        "section": "27",
        "rule": "Delivery of goods and payment of price are concurrent conditions."
    },
    "sale_unfair_trade": {
        "act": "Consumer Affairs Authority Act No. 9 of 2003",
        "section": "18",
        "rule": "Unfair trade practices including false representations are prohibited."
    },

    # ========== MICROFINANCE / LENDING DOMAIN ==========
    "microfinance_license": {
        "act": "Microfinance Act No. 6 of 2016",
        "section": "24",
        "rule": "Microfinance institutions must be licensed to operate legally."
    },
    "microfinance_interest": {
        "act": "Money Lending Ordinance, No. 2 of 1918",
        "section": "10",
        "rule": "Interest rates exceeding legal limits or compound interest clauses may be unenforceable."
    },
    "microfinance_disclosure": {
        "act": "Money Lending Ordinance, No. 2 of 1918",
        "section": "3",
        "rule": "Loan agreements must be in writing and clearly state principal, interest, and terms."
    },
    "microfinance_collection": {
        "act": "Money Lending Ordinance, No. 2 of 1918",
        "section": "15",
        "rule": "Money lenders are not allowed to harass or intimidate borrowers."
    },

    # ========== PAWN / PLEDGE DOMAIN ==========
    "pawn_receipt": {
        "act": "Pawnbrokers Ordinance",
        "section": "15",
        "rule": "Pawnbrokers must provide proper receipt and follow redemption procedures."
    },
    "pawn_redemption": {
        "act": "Pawnbrokers Ordinance",
        "section": "15",
        "rule": "Pledged items must be redeemable within the period specified."
    },
    "pawn_valuation": {
        "act": "Pawnbrokers Ordinance",
        "section": "General",
        "rule": "Proper valuation of pledged items must be done before accepting the pledge."
    },

    # ========== PROPERTY / LAND SALE DOMAIN ==========
    "land_transfer": {
        "act": "Prevention of Frauds Ordinance, No. 7 of 1840",
        "section": "2",
        "rule": "No sale or transfer of land is valid unless in writing, signed, and attested by a notary and two witnesses."
    },
    "land_registration": {
        "act": "Registration of Documents Ordinance",
        "section": "2",
        "rule": "Every deed affecting land must be registered in the appropriate Land Registry."
    },
    "land_description": {
        "act": "Prevention of Frauds Ordinance, No. 7 of 1840",
        "section": "2",
        "rule": "The deed must contain a full description of the property including boundaries and extent."
    },

    # ========== ELECTRONIC CONTRACT / E-COMMERCE DOMAIN ==========
    "econtract_validity": {
        "act": "Electronic Transactions Act, No. 19 of 2006",
        "section": "4",
        "rule": "Electronic contracts are valid and enforceable under certain conditions."
    },
    "esignature": {
        "act": "Electronic Transactions Act, No. 19 of 2006",
        "section": "7",
        "rule": "An electronic signature satisfies a legal requirement for a signature if reliable and appropriate."
    },
    "erecord": {
        "act": "Electronic Transactions Act, No. 19 of 2006",
        "section": "5",
        "rule": "An electronic record satisfies a legal requirement for writing."
    },

    "unknown": {
        "act": "Prevention of Frauds Ordinance",
        "section": "General",
        "rule": "Standard contract clause governed by general contract principles."
    },
}


# ==============================
# STEP 1: Clause Classification
# ==============================
CLAUSE_CATEGORIES = {
    "administrative": {
        "keywords": ["hereinafter", "referred to as", "registration no", "nic:", "signature", 
                    "signed by", "witness", "company seal", "date:", "address:", "name:"],
        "ignore": True
    },
    "identification": {
        "keywords": ["employer", "employee", "party", "parties", "company", "private limited"],
        "laws": []
    },
    "commencement": {
        "keywords": ["commence", "commencement", "start date", "position", "designation", "department"],
        "laws": []
    },
    "probation": {
        "keywords": ["probation", "probationary", "trial period"],
        "laws": ["Termination of Employment of Workmen Act"]
    },
    "salary": {
        "keywords": ["salary", "wage", "remuneration", "pay", "lkr", "rupees", "monthly", "payment"],
        "laws": ["Wages Boards Ordinance", "Employees' Provident Fund Act", "Employees' Trust Fund Act"]
    },
    "epf_etf": {
        "keywords": ["epf", "etf", "provident fund", "trust fund", "contribution"],
        "laws": ["Employees' Provident Fund Act", "Employees' Trust Fund Act"]
    },
    "working_hours": {
        "keywords": ["working hours", "hours of work", "8 hours", "45 hours", "overtime", "rest", "meal"],
        "laws": ["Shop and Office Employees Act"]
    },
    "leave": {
        "keywords": ["leave", "casual leave", "sick leave", "annual leave", "holiday", "vacation", "absence"],
        "laws": ["Shop and Office Employees Act"]
    },
    "maternity": {
        "keywords": ["maternity", "pregnancy", "pregnant", "female employee", "woman", "childbirth", "nursing"],
        "laws": ["Maternity Benefits Ordinance"]
    },
    "public_holiday": {
        "keywords": ["public holiday", "government holiday", "poya", "declared holiday"],
        "laws": ["Shop and Office Employees Act"]
    },
    "termination": {
        "keywords": ["termination", "terminate", "dismiss", "dismissal", "notice period", "end employment"],
        "laws": ["Termination of Employment of Workmen Act", "Industrial Disputes Act"]
    },
    "retrenchment": {
        "keywords": ["retrench", "retrenchment", "redundancy", "layoff", "lay off"],
        "laws": ["Industrial Disputes Act", "Termination of Employment of Workmen Act"]
    },
    "dispute": {
        "keywords": ["dispute", "tribunal", "labour tribunal", "commissioner", "conciliation", "arbitration"],
        "laws": ["Industrial Disputes Act"]
    },
    "confidentiality": {
        "keywords": ["confidential", "confidentiality", "secret", "proprietary", "disclosure"],
        "laws": []
    },
    "ip": {
        "keywords": ["intellectual property", "invention", "patent", "copyright", "design"],
        "laws": []
    },
    "non_compete": {
        "keywords": ["compete", "competing", "competition", "non-compete", "restraint"],
        "laws": []
    },
    "general": {
        "keywords": ["amendment", "entire agreement", "supersede", "assign", "binding"],
        "laws": []
    },
    # RENTAL DOMAIN
    "rent": {
        "keywords": ["rent", "rental", "monthly rent", "advance rent", "landlord", "tenant", "lessee", "lessor"],
        "laws": ["Rent Act"]
    },
    "tenancy": {
        "keywords": ["tenancy", "lease", "premises", "property", "occupy", "occupation", "term"],
        "laws": ["Rent Act", "Registration of Documents Ordinance"]
    },
    "eviction": {
        "keywords": ["eviction", "evict", "vacate", "possession", "ejectment"],
        "laws": ["Rent Act"]
    },
    "security_deposit": {
        "keywords": ["deposit", "security deposit", "advance", "refund"],
        "laws": ["Rent Act"]
    },
    # CONSUMER/LOAN DOMAIN
    "loan": {
        "keywords": ["loan", "borrow", "borrower", "lender", "principal", "interest rate"],
        "laws": ["Money Lending Ordinance", "Consumer Credit Act", "Microfinance Act"]
    },
    "interest": {
        "keywords": ["interest", "rate of interest", "percentage", "per annum", "compound"],
        "laws": ["Money Lending Ordinance"]
    },
    "repayment": {
        "keywords": ["repayment", "installment", "emi", "payment schedule", "due date"],
        "laws": ["Consumer Credit Act"]
    },
    "sale": {
        "keywords": ["sale", "purchase", "buyer", "seller", "goods", "price", "delivery"],
        "laws": ["Sale of Goods Ordinance", "Consumer Affairs Authority Act"]
    },
    "warranty": {
        "keywords": ["warranty", "guarantee", "defect", "quality", "merchantable"],
        "laws": ["Sale of Goods Ordinance", "Consumer Affairs Authority Act"]
    },
    "unfair_terms": {
        "keywords": ["unfair", "unconscionable", "penalty", "forfeiture", "exclusion"],
        "laws": ["Unfair Contract Terms Act", "Consumer Affairs Authority Act"]
    },
    # FINANCE LEASING DOMAIN
    "lease_term": {
        "keywords": ["lease term", "lease period", "lease shall commence", "lease duration", "five years", "60 months", "consecutive months"],
        "laws": ["Finance Leasing Act"]
    },
    "lease_rental": {
        "keywords": ["lease rental", "lease rentals", "monthly lease", "lkr", "rental payment", "lease payment"],
        "laws": ["Finance Leasing Act"]
    },
    "lease_payment": {
        "keywords": ["payment", "bank transfer", "due date", "5th day", "each month", "designated account"],
        "laws": ["Finance Leasing Act"]
    },
    "late_payment_charge": {
        "keywords": ["late payment", "late fee", "overdue", "penalty", "surcharge", "delayed payment"],
        "laws": ["Finance Leasing Act"]
    },
    "early_termination": {
        "keywords": ["early termination", "terminate early", "before completion", "terminates early", "prior written consent"],
        "laws": ["Finance Leasing Act"]
    },
    "repossession": {
        "keywords": ["repossess", "repossession", "seize", "reclaim", "take back", "recover vehicle", "recover equipment"],
        "laws": ["Finance Leasing Act"]
    },
    "vehicle_maintenance": {
        "keywords": ["maintenance", "repairs", "licensing", "roadworthy", "vehicle condition", "care for"],
        "laws": ["Finance Leasing Act"]
    },
    "vehicle_insurance": {
        "keywords": ["insurance", "insure", "comprehensive", "comprehensive insurance", "insurance policy"],
        "laws": ["Finance Leasing Act"]
    },
    "lease_assignment": {
        "keywords": ["assignment", "assign", "transfer rights", "third party", "without notifying"],
        "laws": ["Finance Leasing Act"]
    },
    "lessor_liability": {
        "keywords": ["lessor shall not be liable", "not liable", "no liability", "mechanical defects", "accidents", "damages arising"],
        "laws": ["Finance Leasing Act", "Unfair Contract Terms Act"]
    },
    "lease_dispute": {
        "keywords": ["dispute resolution", "dispute", "decided solely", "final and binding", "waives", "no right to refer"],
        "laws": ["Finance Leasing Act"]
    },
    "lease_governing_law": {
        "keywords": ["governing law", "laws of sri lanka", "governed by", "jurisdiction"],
        "laws": ["Finance Leasing Act"]
    },
    "entire_agreement_lease": {
        "keywords": ["entire agreement", "entire understanding", "supersedes", "prior discussions"],
        "laws": ["Finance Leasing Act"]
    },
    # SALE OF GOODS DOMAIN
    "sale_goods": {
        "keywords": ["sale of goods", "buyer", "seller", "purchase", "goods", "merchandise", "product", "vendor"],
        "laws": ["Sale of Goods Ordinance", "Consumer Affairs Authority Act"]
    },
    "merchantable_quality": {
        "keywords": ["merchantable quality", "quality", "defect", "defective", "fit for purpose", "fitness"],
        "laws": ["Sale of Goods Ordinance"]
    },
    "sale_delivery": {
        "keywords": ["delivery", "deliver", "shipment", "shipping", "dispatch", "transit"],
        "laws": ["Sale of Goods Ordinance"]
    },
    "sale_unfair_trade": {
        "keywords": ["unfair trade", "false representation", "misleading", "deceptive"],
        "laws": ["Consumer Affairs Authority Act"]
    },
    # MICROFINANCE / LENDING DOMAIN
    "microfinance_license": {
        "keywords": ["microfinance", "micro finance", "mfi", "licensed", "microfinance institution"],
        "laws": ["Microfinance Act"]
    },
    "microfinance_interest": {
        "keywords": ["interest rate", "rate of interest", "annual rate", "per annum", "flat rate", "reducing balance"],
        "laws": ["Money Lending Ordinance"]
    },
    "microfinance_disclosure": {
        "keywords": ["disclosure", "total cost", "fees", "charges", "apr", "annual percentage"],
        "laws": ["Money Lending Ordinance"]
    },
    "microfinance_collection": {
        "keywords": ["collection", "recovery", "harassment", "intimidation", "debt collector"],
        "laws": ["Money Lending Ordinance"]
    },
    # PAWN / PLEDGE DOMAIN
    "pawn_receipt": {
        "keywords": ["pawn", "pawnbroker", "pledge", "pledged", "pawn ticket", "receipt"],
        "laws": ["Pawnbrokers Ordinance"]
    },
    "pawn_redemption": {
        "keywords": ["redeem", "redemption", "reclaim", "return of pledge", "forfeit"],
        "laws": ["Pawnbrokers Ordinance"]
    },
    "pawn_valuation": {
        "keywords": ["valuation", "appraisal", "assessed value", "gold", "jewelry", "jewellery"],
        "laws": ["Pawnbrokers Ordinance"]
    },
    # PROPERTY / LAND SALE DOMAIN
    "land_transfer": {
        "keywords": ["transfer", "conveyance", "deed of transfer", "sale of land", "vendor", "vendee", "purchaser"],
        "laws": ["Prevention of Frauds Ordinance", "Registration of Documents Ordinance"]
    },
    "land_registration": {
        "keywords": ["registration", "land registry", "registered", "registrar of lands", "folio"],
        "laws": ["Registration of Documents Ordinance"]
    },
    "land_description": {
        "keywords": ["boundaries", "extent", "plan number", "lot number", "survey", "perches", "acres", "hectares"],
        "laws": ["Prevention of Frauds Ordinance"]
    },
    # ELECTRONIC CONTRACT / E-COMMERCE DOMAIN
    "econtract_validity": {
        "keywords": ["electronic contract", "online agreement", "e-commerce", "digital contract", "click-wrap", "browse-wrap"],
        "laws": ["Electronic Transactions Act"]
    },
    "esignature": {
        "keywords": ["electronic signature", "e-signature", "digital signature", "electronically signed"],
        "laws": ["Electronic Transactions Act"]
    },
    "erecord": {
        "keywords": ["electronic record", "digital record", "electronic document", "electronic form"],
        "laws": ["Electronic Transactions Act"]
    },
}


def classify_clause(clause_text, domain=None):
    """Classify a clause into a category with domain awareness"""
    clause_lower = clause_text.lower()
    
    # Domain-specific priority categories
    domain_priority = {
        "rental": ["rent", "tenancy", "eviction", "security_deposit", "maintenance", "subletting"],
        "consumer": ["loan", "interest", "repayment", "sale", "warranty", "hire_purchase"],
        "employment": ["salary", "epf_etf", "working_hours", "leave", "termination", "maternity"],
        "finance_leasing": ["lease_term", "lease_rental", "lease_payment", "late_payment_charge", 
                            "early_termination", "repossession", "vehicle_maintenance", "vehicle_insurance",
                            "lease_assignment", "lessor_liability", "lease_dispute", "lease_governing_law"],
        "sale_of_goods": ["sale_goods", "merchantable_quality", "sale_delivery", "sale_unfair_trade"],
        "microfinance": ["microfinance_license", "microfinance_interest", "microfinance_disclosure", "microfinance_collection"],
        "pawn_pledge": ["pawn_receipt", "pawn_redemption", "pawn_valuation"],
        "land_property": ["land_transfer", "land_registration", "land_description"],
        "electronic_contract": ["econtract_validity", "esignature", "erecord"]
    }
    
    # Check domain-specific categories first
    if domain and domain in domain_priority:
        for category in domain_priority[domain]:
            if category in CLAUSE_CATEGORIES:
                config = CLAUSE_CATEGORIES[category]
                for keyword in config.get("keywords", []):
                    if keyword in clause_lower:
                        return category, config
    
    # Then check all categories
    for category, config in CLAUSE_CATEGORIES.items():
        for keyword in config.get("keywords", []):
            if keyword in clause_lower:
                return category, config
    
    return "unknown", {"keywords": [], "laws": [], "ignore": False}


def is_administrative_clause(clause_text):
    """Check if clause is just administrative/boilerplate"""
    clause_lower = clause_text.lower()
    
    admin_patterns = [
        r"^\s*(signed|signature|witness|date|address|name)\s*[:.]",
        r"^\s*no\.\s*\d+",
        r"nic:\s*\d+",
        r"company\s+seal",
        r"^\s*---+\s*$",
        r"registration\s+no",
        r"^\*+[A-Z\s]+\*+$",
        r"^[A-Z\s]+:$",
    ]
    
    for pattern in admin_patterns:
        if re.search(pattern, clause_lower, re.IGNORECASE):
            return True
    
    if len(clause_text.strip()) < 50:
        return True
    
    return False


# ==============================
# STEP 2: Domain Detection
# ==============================
def detect_domain(text):
    """Detect document domain"""
    text_lower = text.lower()
    
    # Employment keywords
    employment_keywords = ["employee", "employer", "salary", "employment", "epf", "etf", 
                          "termination", "probation", "working hours", "leave", "maternity",
                          "wages board", "shop and office", "industrial dispute"]
    
    # Finance Leasing keywords - MUST CHECK BEFORE rental (they share some terms)
    finance_leasing_keywords = ["finance lease", "finance leasing", "leasing agreement", 
                                "vehicle", "motor vehicle", "equipment", "machinery",
                                "lease rental", "lease rentals", "monthly lease",
                                "repossession", "repossess", "leasing company",
                                "finance company", "financial institution",
                                "lease term", "lessee shall pay", "lessor may",
                                "hire purchase", "asset finance", "equipment lease",
                                "vehicle lease", "leased asset", "leased equipment",
                                "leased vehicle", "insurance of vehicle",
                                "registration of vehicle", "comprehensive insurance"]
    
    # Rental keywords - for property/premises rental (Rent Act)
    rental_keywords = ["tenant", "landlord", "premises", "tenancy", 
                      "accommodation", "dwelling", "apartment",
                      "flat", "house", "property", "occupancy", "eviction", "evict",
                      "monthly rent", "advance rent", "security deposit", "vacate",
                      "rent act", "residential", "tenanted", "occupied",
                      "tenancy agreement", "rental property", "rented premises"]
    
    # Consumer/Loan keywords - comprehensive list
    consumer_keywords = ["loan", "borrower", "lender", "interest", "principal", "buyer", 
                        "seller", "goods", "credit", "mortgage", "installment", "emi",
                        "repayment", "debt", "consumer", "purchase", "sale agreement",
                        "money lending", "banking", "collateral"]
    
    # Partnership keywords
    partnership_keywords = ["partnership", "partner", "partners", "profit sharing", "loss sharing",
                           "partnership deed", "partnership agreement", "joint venture",
                           "partnership firm", "partnership business", "capital contribution",
                           "profit ratio", "loss ratio", "dissolution", "winding up"]
    
    # Sale of Goods keywords
    sale_of_goods_keywords = ["sale of goods", "buyer", "seller", "goods", "merchandise",
                             "product", "merchantable quality", "fitness for purpose",
                             "delivery of goods", "sale agreement", "purchase order",
                             "supply agreement", "vendor", "defective goods",
                             "implied warranty", "sale price", "consumer goods"]
    
    # Microfinance / Lending keywords
    microfinance_keywords = ["microfinance", "micro finance", "mfi", "micro lending",
                            "micro loan", "small loan", "group lending",
                            "microfinance institution", "microfinance act",
                            "money lender", "money lending", "licensed lender",
                            "promissory note", "pawn ticket"]
    
    # Pawn / Pledge keywords
    pawn_pledge_keywords = ["pawn", "pawnbroker", "pledge", "pledged", "pawn ticket",
                           "redemption", "redeem", "pawned", "pawn shop",
                           "pledged item", "gold pledge", "jewelry pledge",
                           "forfeiture", "unredeemed"]
    
    # Property / Land Sale keywords
    land_property_keywords = ["land", "deed", "conveyance", "transfer of land",
                             "vendee", "notary", "boundaries", "survey plan",
                             "perches", "acres", "title deed", "encumbrance",
                             "land registry", "immovable property", "sale of land",
                             "deed of transfer", "prevention of frauds"]
    
    # Electronic Contract / E-commerce keywords
    electronic_contract_keywords = ["electronic contract", "e-commerce", "online agreement",
                                   "digital contract", "electronic signature", "e-signature",
                                   "click-wrap", "browse-wrap", "terms of service",
                                   "online terms", "website terms", "digital transaction",
                                   "electronic transaction", "online purchase"]
    
    # Strong indicators that override general scoring - CHECK IN PRIORITY ORDER
    if "partnership agreement" in text_lower or "partnership deed" in text_lower:
        return "partnership"
    if "pawnbroker" in text_lower or "pawn ticket" in text_lower or "pledge agreement" in text_lower:
        return "pawn_pledge"
    if "microfinance" in text_lower or "micro finance" in text_lower or "micro lending" in text_lower:
        return "microfinance"
    if "deed of transfer" in text_lower or "sale of land" in text_lower or "conveyance" in text_lower:
        return "land_property"
    if "electronic contract" in text_lower or "e-commerce agreement" in text_lower or "click-wrap" in text_lower:
        return "electronic_contract"
    if "sale of goods" in text_lower or "supply agreement" in text_lower or "purchase order" in text_lower:
        return "sale_of_goods"
    
    # Finance Leasing - check for various patterns including "finance leasing agreement"
    if ("finance lease" in text_lower or "finance leasing" in text_lower or 
        "leasing agreement" in text_lower or "vehicle lease" in text_lower or
        "lease rental" in text_lower or "lease rentals" in text_lower or
        "repossess" in text_lower or "leased vehicle" in text_lower or
        "leased equipment" in text_lower or "leased asset" in text_lower or
        ("lessor" in text_lower and "lessee" in text_lower and "vehicle" in text_lower) or
        ("lessor" in text_lower and "lessee" in text_lower and "lease" in text_lower and "rental" in text_lower)):
        return "finance_leasing"
    
    if "rent act" in text_lower or "tenancy agreement" in text_lower:
        return "rental"
    if "loan agreement" in text_lower or "money lending" in text_lower or "credit agreement" in text_lower:
        return "consumer"
    if "employment agreement" in text_lower or "employment contract" in text_lower:
        return "employment"
    
    # Calculate scores
    employment_score = sum(1 for kw in employment_keywords if kw in text_lower)
    finance_leasing_score = sum(1 for kw in finance_leasing_keywords if kw in text_lower)
    rental_score = sum(1 for kw in rental_keywords if kw in text_lower)
    consumer_score = sum(1 for kw in consumer_keywords if kw in text_lower)
    partnership_score = sum(1 for kw in partnership_keywords if kw in text_lower)
    
    # Boost finance_leasing if "lessor" and "lessee" appear with vehicle/equipment terms
    if ("lessor" in text_lower and "lessee" in text_lower):
        if any(kw in text_lower for kw in ["vehicle", "equipment", "machinery", "repossess", "lease rental"]):
            finance_leasing_score += 5
    
    # Calculate scores for new domains
    sale_of_goods_score = sum(1 for kw in sale_of_goods_keywords if kw in text_lower)
    microfinance_score = sum(1 for kw in microfinance_keywords if kw in text_lower)
    pawn_pledge_score = sum(1 for kw in pawn_pledge_keywords if kw in text_lower)
    land_property_score = sum(1 for kw in land_property_keywords if kw in text_lower)
    electronic_contract_score = sum(1 for kw in electronic_contract_keywords if kw in text_lower)
    
    # Choose the highest score
    scores = {
        "employment": employment_score, 
        "finance_leasing": finance_leasing_score,
        "rental": rental_score, 
        "consumer": consumer_score,
        "partnership": partnership_score,
        "sale_of_goods": sale_of_goods_score,
        "microfinance": microfinance_score,
        "pawn_pledge": pawn_pledge_score,
        "land_property": land_property_score,
        "electronic_contract": electronic_contract_score
    }
    max_domain = max(scores, key=scores.get)
    
    # Return the domain with highest score, or general if all are 0
    if scores[max_domain] > 0:
        return max_domain
    return "general"


# ==============================
# STEP 3: ILLEGAL Clause Patterns (Domain-Specific)
# ==============================
ILLEGAL_PATTERNS = {
    "employment": [
        {
            "pattern": r"(not\s+entitled|shall\s+not\s+be\s+entitled|no\s+entitlement|does\s+not\s+provide).{0,50}(maternity|maternity\s+leave|maternity\s+benefits)",
            "act": "Maternity Benefits Ordinance",
            "section": "2",
            "rule": "Every woman worker is entitled to maternity benefits. This is a statutory right that cannot be contracted away.",
            "recommendation": "ILLEGAL: Denying maternity leave violates the Maternity Benefits Ordinance. Female employees MUST be entitled to 84 working days maternity leave."
        },
        {
            "pattern": r"(not\s+entitled|shall\s+not\s+be\s+entitled).{0,50}(public\s+holiday|government.{0,20}holiday|declared\s+holiday|poya)",
            "act": "Shop and Office Employees Act",
            "section": "7(1)",
            "rule": "An employee must be given paid public holidays, up to 9 days per year.",
            "recommendation": "ILLEGAL: Employees MUST be entitled to public holidays or double pay/leave in lieu."
        },
        {
            "pattern": r"(no\s+right\s+to\s+dispute|no\s+right\s+to\s+challenge|shall\s+have\s+no\s+right).{0,50}(dispute|challenge|forum|tribunal)",
            "act": "Industrial Disputes Act",
            "section": "31B(1)(a) & 47A",
            "rule": "Employees have the legal right to challenge termination. Contract clauses cannot limit worker rights.",
            "recommendation": "ILLEGAL: The right to access labour tribunals is STATUTORY and cannot be waived. This clause is VOID."
        },
        {
            "pattern": r"(waive|waives|waiving|relinquish).{0,30}(right|rights).{0,30}(tribunal|labour\s+tribunal|legal|court)",
            "act": "Industrial Disputes Act",
            "section": "31B(1)(a) & 47A",
            "rule": "Employees have the legal right to challenge termination. Contract clauses cannot limit worker rights.",
            "recommendation": "ILLEGAL: Statutory rights cannot be waived by contract. This waiver is unenforceable."
        },
        {
            "pattern": r"(agrees?\s+not\s+to\s+challenge|shall\s+not\s+challenge|cannot\s+challenge).{0,50}(termination|dismissal|dispute|decision)",
            "act": "Industrial Disputes Act",
            "section": "31B(1)(a)",
            "rule": "Employees have the legal right to challenge termination by applying to a labour tribunal.",
            "recommendation": "ILLEGAL: The right to challenge decisions in legal forums cannot be contractually excluded."
        },
        {
            "pattern": r"(terminate|termination|dismiss).{0,30}(24\s+hours?|immediate).{0,30}(any\s+reason|no\s+reason|whatsoever|for\s+any\s+reason)",
            "act": "Termination of Employment of Workmen Act",
            "section": "2(1)",
            "rule": "An employer must not terminate without worker consent or Labour Commissioner approval.",
            "recommendation": "ILLEGAL: Arbitrary termination with 24 hours notice for 'any reason' violates the Termination Act."
        },
        {
            "pattern": r"(application|complaint|filed|submit).{0,30}(14|fourteen)\s+days.{0,30}(termination|tribunal)",
            "act": "Industrial Disputes Act",
            "section": "31B(7)",
            "rule": "Complaints about termination must be filed within SIX MONTHS.",
            "recommendation": "ILLEGAL: The statutory limit is 6 MONTHS, not 14 days. This clause is void."
        },
        {
            "pattern": r"(no\s+industrial\s+dispute|no\s+dispute).{0,30}(referred|refer).{0,30}(commissioner|labour)",
            "act": "Industrial Disputes Act",
            "section": "2",
            "rule": "The Commissioner must investigate any industrial dispute.",
            "recommendation": "ILLEGAL: The Commissioner's statutory authority cannot be excluded by contract."
        },
        {
            "pattern": r"(not\s+subject\s+to|shall\s+not\s+be\s+subject).{0,30}(conciliation|arbitration|tribunal\s+proceedings)",
            "act": "Industrial Disputes Act",
            "section": "3",
            "rule": "The Commissioner may refer disputes for conciliation, arbitration, or tribunal.",
            "recommendation": "ILLEGAL: Statutory dispute resolution cannot be contractually excluded."
        },
        {
            "pattern": r"(employer|employer's).{0,20}(sole|final|absolute|exclusive).{0,20}(authority|decision).{0,20}(dispute|disputes)",
            "act": "Industrial Disputes Act",
            "section": "2 & 3",
            "rule": "Independent dispute resolution exists by law.",
            "recommendation": "ILLEGAL: Employers cannot be the sole authority on disputes."
        },
        {
            "pattern": r"(settlement|dispute).{0,30}(valid|sufficient|binding).{0,30}(verbal|not\s+in\s+writing|not\s+recorded|not.{0,10}signed)",
            "act": "Industrial Disputes Act",
            "section": "12",
            "rule": "A settlement must be in writing and signed by both parties.",
            "recommendation": "ILLEGAL: Verbal settlements are not valid. Must be written and signed."
        },
        {
            "pattern": r"(retrench|retrenchment).{0,30}(immediate|immediately|without\s+notice|without\s+prior\s+notice|verbal)",
            "act": "Industrial Disputes Act",
            "section": "31F & 31G",
            "rule": "Employers must give written notice. Retrenchment cannot occur until 2 months after notice.",
            "recommendation": "ILLEGAL: Retrenchment requires WRITTEN notice and 2-MONTH waiting period."
        },
        {
            "pattern": r"(hire|hiring|employ).{0,30}(without|no).{0,20}(preference|priority).{0,30}(retrenched|previously)",
            "act": "Industrial Disputes Act",
            "section": "50",
            "rule": "Retrenched workers must be given priority when rehiring.",
            "recommendation": "ILLEGAL: Previously retrenched workers have statutory rehiring priority."
        },
        {
            "pattern": r"(disciplined|terminated|penalized|punished|dismiss).{0,40}(providing\s+evidence|giving\s+evidence|testimony|witness|legal\s+proceedings)",
            "act": "Industrial Disputes Act",
            "section": "40(1)(j)",
            "rule": "Employers cannot punish workers for participating in legal proceedings.",
            "recommendation": "ILLEGAL: Retaliation for participating in legal proceedings is a CRIMINAL offense."
        },
        {
            "pattern": r"(terminated|penalized|punished|terminate|penalize|punish|dismiss).{0,40}(claiming|claim|exercising|exercise).{0,40}(collective\s+agreement|tribunal|rights|benefits|statutory\s+rights|tribunal.?awarded)",
            "act": "Industrial Disputes Act",
            "section": "40(1)(k) & 47A",
            "rule": "Retaliation against employees for claiming collective agreement benefits or tribunal-awarded rights is ILLEGAL.",
            "recommendation": "ILLEGAL: This clause violates Industrial Disputes Act Section 40 and 47A. Retaliation for exercising statutory rights is a criminal offense."
        },
        {
            "pattern": r"(employer|company).{0,30}(may|shall|can).{0,30}(terminate|penalize|punish|dismiss).{0,40}(claiming|exercising).{0,30}(collective|tribunal|statutory|rights|benefits)",
            "act": "Industrial Disputes Act",
            "section": "40 & 47A",
            "rule": "Employers cannot penalize employees for exercising statutory rights.",
            "recommendation": "ILLEGAL: This clause is VOID. Retaliation for claiming statutory rights violates Sections 40 and 47A."
        },
        {
            "pattern": r"(clause|contract|agreement|provision).{0,30}(limiting|limit|modify|override|restrict|waive).{0,30}(worker\s+rights|statutory|labour|employee\s+rights).{0,20}(valid|enforceable|binding)",
            "act": "Industrial Disputes Act",
            "section": "47A",
            "rule": "Any contract clause that limits worker rights under this Act is INVALID and VOID.",
            "recommendation": "ILLEGAL: This clause is VOID under Section 47A. Statutory worker rights cannot be limited by contract."
        },
        {
            "pattern": r"(any|all).{0,20}(clause|contract|agreement).{0,30}(limiting|limit).{0,30}(worker|employee).{0,20}(rights|statutory).{0,20}(shall\s+be|is|are).{0,20}(valid|enforceable)",
            "act": "Industrial Disputes Act",
            "section": "47A",
            "rule": "This statement is legally FALSE. Any clause limiting statutory worker rights is VOID.",
            "recommendation": "ILLEGAL: This clause is VOID. Under Section 47A, clauses limiting worker rights are INVALID, not valid."
        },
        {
            "pattern": r"(during\s+probation|probation\s+period|probationary).{0,40}(terminate|termination|dismiss|dismissal).{0,30}(immediately|instant|without\s+notice|without\s+inquiry|without\s+justification|without\s+cause|at\s+will)",
            "act": "Industrial Disputes Act",
            "section": "31B",
            "rule": "Even during probation, if the employee is a 'workman' under the Act, arbitrary termination without cause may be challengeable under Section 31B.",
            "recommendation": "CAUTION: Probation does not give unlimited termination rights. If employee is a 'workman', termination may still be challenged under Industrial Disputes Act Section 31B."
        },
        {
            "pattern": r"(summary\s+dismissal|immediate\s+dismissal|dismiss.{0,20}immediately).{0,30}(without\s+investigation|without\s+hearing|without\s+inquiry|no\s+investigation|no\s+opportunity)",
            "act": "Termination of Employment of Workmen Act",
            "section": "2(5)",
            "rule": "Employers must give written reasons for disciplinary termination.",
            "recommendation": "ILLEGAL: Dismissal requires investigation and opportunity to be heard."
        },
        {
            "pattern": r"(no\s+compensation|without\s+compensation).{0,30}(retrenchment|retrenched)",
            "act": "Termination of Employment of Workmen Act",
            "section": "2(2)(e)",
            "rule": "Commissioner may set terms including compensation.",
            "recommendation": "ILLEGAL: Retrenchment compensation may be required. Blanket exclusion is invalid."
        },
    ],
    "rental": [
        {
            "pattern": r"(advance\s+rent|rent\s+in\s+advance|advance\s+payment).{0,40}(exceed|more\s+than|equal\s+to).{0,20}(4|four|5|five|6|six|12|twelve)\s+months?",
            "act": "Rent Act",
            "section": "9(1)(a)",
            "rule": "No landlord shall demand or receive any premium, key money, or advance rent exceeding 3 months of standard rent.",
            "recommendation": "ILLEGAL: Advance rent cannot exceed 3 months under Section 9(1)(a) of the Rent Act."
        },
        {
            "pattern": r"(advance).{0,20}(6|six|twelve|12)\s+months?",
            "act": "Rent Act",
            "section": "9(1)(a)",
            "rule": "Advance rent shall not exceed three months of the standard rent.",
            "recommendation": "ILLEGAL: Demanding more than 3 months advance rent violates Section 9 of the Rent Act."
        },
        {
            "pattern": r"(key\s+money|goodwill|premium).{0,30}(required|demand|pay|payment|shall\s+pay)",
            "act": "Rent Act",
            "section": "9",
            "rule": "Key money, goodwill, or premium payments are restricted under the Rent Act.",
            "recommendation": "ILLEGAL: Demanding key money or premium exceeding legal limits violates Section 9."
        },
        {
            "pattern": r"(evict|eviction|eject|vacate|remove\s+tenant).{0,40}(immediate|immediately|without\s+notice|without\s+cause|any\s+reason|at\s+will|forthwith)",
            "act": "Rent Act",
            "section": "22",
            "rule": "A landlord may only obtain possession through court order on grounds specified in Section 22.",
            "recommendation": "ILLEGAL: Arbitrary eviction without court order and valid grounds violates Section 22 of the Rent Act."
        },
        {
            "pattern": r"(landlord|lessor|owner).{0,20}(right|entitled|may).{0,30}(evict|eject|remove|terminate\s+tenancy).{0,30}(without\s+reason|any\s+reason|sole\s+discretion)",
            "act": "Rent Act",
            "section": "22(1)",
            "rule": "Eviction requires valid grounds such as non-payment, breach of conditions, or landlord's reasonable requirement.",
            "recommendation": "ILLEGAL: Landlord cannot evict at will. Must prove valid grounds under Section 22(1)."
        },
        {
            "pattern": r"(landlord|lessor|owner).{0,30}(increase|raise|revise|change)\s+rent.{0,30}(any\s+time|at\s+will|without\s+notice|unilateral|sole\s+discretion)",
            "act": "Rent Act",
            "section": "10",
            "rule": "Rent increases are regulated and must follow procedures under Section 10.",
            "recommendation": "ILLEGAL: Unilateral rent increases without proper procedure violate Section 10 of the Rent Act."
        },
        {
            "pattern": r"(rent).{0,20}(increase|revised).{0,30}(without\s+consent|automatically|unilaterally|exceed.{0,20}10\s*%)",
            "act": "Rent Act",
            "section": "10",
            "rule": "Rent increase provisions are regulated and cannot exceed prescribed limits.",
            "recommendation": "ILLEGAL: Automatic or excessive rent increases violate Rent Act Section 10."
        },
        {
            "pattern": r"(tenant|lessee).{0,30}(waive|waives|forfeit|surrender|give\s+up).{0,30}(rights?|protection|statutory|legal|rent\s+act)",
            "act": "Rent Act",
            "section": "32",
            "rule": "Any agreement contracting out of the provisions of the Rent Act is void.",
            "recommendation": "ILLEGAL: Agreements requiring tenants to waive Rent Act protections are void under Section 32."
        },
        {
            "pattern": r"(tenant|lessee).{0,30}(no\s+right|shall\s+not\s+have|not\s+entitled).{0,30}(court|tribunal|legal|challenge|contest|rent\s+board)",
            "act": "Rent Act",
            "section": "32",
            "rule": "Tenants cannot be deprived of their legal rights under the Rent Act.",
            "recommendation": "ILLEGAL: Tenants' right to legal remedies cannot be excluded. Void under Section 32."
        },
        {
            "pattern": r"(security\s+deposit|deposit|advance).{0,30}(non-refundable|not\s+refund|forfeit|forfeited\s+automatically|not\s+return)",
            "act": "Rent Act",
            "section": "9",
            "rule": "Deposits must be refundable subject to lawful deductions for damages.",
            "recommendation": "ILLEGAL: Non-refundable deposits violate tenant protections under Section 9."
        },
        {
            "pattern": r"(landlord|lessor|owner).{0,30}(enter|access|inspect|come\s+into).{0,30}(any\s+time|without\s+notice|at\s+will|whenever)",
            "act": "Rent Act",
            "section": "15",
            "rule": "Landlord must give reasonable notice before entering premises except in emergencies.",
            "recommendation": "ILLEGAL: Landlords must give reasonable notice before entering. Section 15 protects tenant's quiet enjoyment."
        },
        {
            "pattern": r"(tenant|lessee).{0,30}(responsible|liable).{0,30}(all\s+repairs|structural\s+repairs|major\s+repairs|roof|foundation)",
            "act": "Rent Act",
            "section": "16",
            "rule": "Landlord is responsible for keeping the premises in good tenantable repair.",
            "recommendation": "ILLEGAL: Structural repairs are landlord's responsibility under Section 16 of the Rent Act."
        },
        {
            "pattern": r"(termination|terminate|end\s+lease).{0,30}(immediate|without\s+notice|24\s+hours?|forthwith)",
            "act": "Rent Act",
            "section": "22",
            "rule": "Termination requires proper notice and valid grounds under Section 22.",
            "recommendation": "ILLEGAL: Immediate termination without proper notice and grounds violates Section 22."
        },
        {
            "pattern": r"(landlord|lessor).{0,30}(cut|disconnect|stop|withdraw).{0,30}(water|electricity|utilities|services|essential)",
            "act": "Rent Act",
            "section": "17",
            "rule": "Landlord must provide essential services. Disconnection as coercion is prohibited.",
            "recommendation": "ILLEGAL: Disconnecting essential services violates Section 17 of the Rent Act."
        },
        {
            "pattern": r"(rent\s+act|statutory\s+protections).{0,30}(shall\s+not\s+apply|does\s+not\s+apply|excluded|waived)",
            "act": "Rent Act",
            "section": "32",
            "rule": "The Rent Act applies to all residential premises regardless of contractual provisions.",
            "recommendation": "ILLEGAL: Rent Act protections cannot be contracted out. Such clauses are void under Section 32."
        },
        {
            "pattern": r"(lease|tenancy).{0,30}(not\s+registered|need\s+not\s+be\s+registered|registration\s+not\s+required).{0,30}(more\s+than|exceed|over)\s+(one|1)\s+year",
            "act": "Registration of Documents Ordinance",
            "section": "2",
            "rule": "Leases exceeding one year must be registered to be valid against third parties.",
            "recommendation": "NOTE: Leases over 1 year should be registered under the Registration of Documents Ordinance."
        },
        {
            "pattern": r"(landlord|lessor).{0,30}(no\s+obligation|not\s+required|not\s+liable).{0,30}(receipt|rent\s+receipt|acknowledge)",
            "act": "Rent Act",
            "section": "33",
            "rule": "Landlord must provide receipt for rent payments when requested by tenant.",
            "recommendation": "ILLEGAL: Landlords must provide rent receipts as required by Section 33 of the Rent Act."
        },
    ],
    "finance_leasing": [
        {
            "pattern": r"(repossess|repossession|seize|reclaim).{0,40}(without\s+notice|without\s+prior\s+notice|immediately|without\s+court)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "21(1)",
            "rule": "Before enforcing default rights, the lessor must serve a written notice specifying the default and a timeline to fix it.",
            "recommendation": "ILLEGAL: Repossession without prior written notice violates Section 21(1) of the Finance Leasing Act. Lessor must give notice specifying the default and reasonable time to remedy."
        },
        {
            "pattern": r"(lessee).{0,30}(waive|waives|surrender|forfeit|relinquish).{0,30}(right|rights).{0,30}(court|tribunal|legal|arbitration|regulatory|complain)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "General",
            "rule": "Lessees cannot be required to waive their legal rights and access to courts.",
            "recommendation": "ILLEGAL: Clauses requiring lessees to waive their right to legal remedies are void. Access to courts is a constitutional right."
        },
        {
            "pattern": r"(dispute|disputes).{0,30}(decided\s+solely|determined\s+solely|solely\s+by).{0,30}(lessor|company|lender).{0,30}(final|binding)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "General",
            "rule": "Dispute resolution must be fair; one party cannot be the sole arbiter.",
            "recommendation": "ILLEGAL: Lessor cannot be the sole decision-maker on disputes. This violates principles of natural justice."
        },
        {
            "pattern": r"(no\s+right\s+to\s+refer|waives.{0,20}right\s+to\s+refer|shall\s+not\s+refer).{0,30}(court|arbitration|tribunal|regulatory\s+authority)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "General",
            "rule": "Access to legal remedies cannot be contractually excluded.",
            "recommendation": "ILLEGAL: This clause attempts to exclude access to courts and regulatory bodies, which is void."
        },
        {
            "pattern": r"(late\s+payment|overdue).{0,30}(charge|fee|penalty).{0,20}(3[5-9]|[4-9][0-9]|100)\s*%",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "20",
            "rule": "Late payment charges must be reasonable and proportionate.",
            "recommendation": "POTENTIALLY ILLEGAL: Late payment charges of 35% or more are excessive and may be challenged as unconscionable."
        },
        {
            "pattern": r"(terminates?\s+early|early\s+termination).{0,40}(pay\s+all|immediately\s+pay|lump\s+sum).{0,30}(remaining|entire|full\s+lease)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "20",
            "rule": "Early termination penalties must be reasonable and reflect actual loss.",
            "recommendation": "REVIEW: Requiring payment of ALL remaining rentals on early termination may be excessive. Early settlement should provide appropriate rebate."
        },
        {
            "pattern": r"(lessor|company).{0,30}(shall\s+not\s+be\s+liable|not\s+liable|no\s+liability).{0,30}(any\s+circumstances|under\s+any|whatsoever|all\s+circumstances)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "11(1)",
            "rule": "The lessee has a right to peaceful possession; complete exclusion of lessor liability may be unreasonable.",
            "recommendation": "REVIEW: Complete exclusion of lessor liability 'under any circumstances' may be unreasonable under the Unfair Contract Terms Act."
        },
        {
            "pattern": r"(no\s+complaint|shall\s+not\s+complain|agrees\s+not\s+to\s+complain).{0,30}(authority|regulatory|government|lessor)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "General",
            "rule": "Lessees retain the right to complain to regulatory authorities.",
            "recommendation": "ILLEGAL: This clause attempts to prevent complaints to authorities, which is void."
        },
        {
            "pattern": r"(lessor|company|financial\s+institution).{0,30}(assign|transfer).{0,30}(without\s+notifying|without\s+consent|without\s+notice).{0,20}(lessee)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "3",
            "rule": "Assignment of lease rights should be disclosed to ensure lessee knows who to deal with.",
            "recommendation": "REVIEW: Assignment without notifying lessee may create practical difficulties. Fair practice requires notification."
        },
        {
            "pattern": r"(default|defaulting).{0,30}(more\s+than\s+seven|7)\s+days.{0,30}(immediately\s+repossess|repossess\s+without)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "21(1)",
            "rule": "Before enforcing default rights, lessor must serve written notice with timeline to remedy.",
            "recommendation": "ILLEGAL: 7-day default triggering immediate repossession without proper notice violates Section 21(1). Written notice with reasonable cure period is required."
        },
    ],
    "consumer": [
        {
            "pattern": r"(interest\s+rate|rate\s+of\s+interest|interest).{0,30}(exceed|more\s+than|above).{0,20}(25|30|35|40|50|100)\s*(%|percent|per\s+cent)",
            "act": "Money Lending Ordinance",
            "section": "10",
            "rule": "Courts may reopen money lending transactions with excessive or unconscionable interest rates.",
            "recommendation": "POTENTIALLY ILLEGAL: Excessive interest rates may be reopened by court under Section 10."
        },
        {
            "pattern": r"(compound\s+interest|interest\s+on\s+interest).{0,30}(charged|applied|calculated|payable)",
            "act": "Money Lending Ordinance",
            "section": "11",
            "rule": "Compound interest on loans may be restricted and unenforceable.",
            "recommendation": "REVIEW: Compound interest provisions may be unenforceable under Section 11."
        },
        {
            "pattern": r"(borrower|consumer|buyer|debtor).{0,30}(waive|waives|forfeit|surrender).{0,30}(rights?|consumer\s+protection|statutory|legal)",
            "act": "Consumer Affairs Authority Act",
            "section": "10",
            "rule": "Consumer rights under the Act cannot be waived or contracted out.",
            "recommendation": "ILLEGAL: Consumer protection rights cannot be waived. Void under Section 10."
        },
        {
            "pattern": r"(borrower|debtor|consumer).{0,30}(no\s+right|shall\s+not|cannot).{0,30}(court|tribunal|legal|challenge|dispute|complain)",
            "act": "Consumer Affairs Authority Act",
            "section": "31",
            "rule": "Consumers have the right to make complaints and seek remedies.",
            "recommendation": "ILLEGAL: Consumer's right to legal remedies cannot be excluded."
        },
        {
            "pattern": r"(exclusion|exclude|exempt|no\s+liability|not\s+liable).{0,30}(death|personal\s+injury|negligence)",
            "act": "Unfair Contract Terms Act",
            "section": "2",
            "rule": "Exclusion clauses for negligence causing death or personal injury are void.",
            "recommendation": "ILLEGAL: Exclusion of liability for death or personal injury from negligence is void."
        },
        {
            "pattern": r"(exclusion|exclude|exempt|no\s+liability).{0,30}(liability|responsibility).{0,30}(defect|damage|loss|injury|harm)",
            "act": "Unfair Contract Terms Act",
            "section": "2",
            "rule": "Unreasonable exclusion clauses for other loss or damage may be void.",
            "recommendation": "POTENTIALLY ILLEGAL: Blanket exclusion of liability may be void under Section 2."
        },
        {
            "pattern": r"(implied\s+warrant|merchantable\s+quality|fit\s+for\s+purpose|fitness).{0,30}(exclude|excluded|waive|waived|not\s+apply|does\s+not\s+apply)",
            "act": "Sale of Goods Ordinance",
            "section": "14-15",
            "rule": "Implied conditions as to merchantable quality and fitness for purpose apply to consumer sales.",
            "recommendation": "ILLEGAL: Implied warranties under Sections 14-15 cannot be excluded in consumer sales."
        },
        {
            "pattern": r"(seller|vendor|supplier).{0,30}(no\s+warranty|no\s+guarantee|no\s+liability|not\s+liable).{0,30}(title|ownership|encumbrance)",
            "act": "Sale of Goods Ordinance",
            "section": "13",
            "rule": "Seller must have right to sell and goods must be free from encumbrances.",
            "recommendation": "ILLEGAL: Implied warranty of title under Section 13 cannot be excluded."
        },
        {
            "pattern": r"(seller|vendor|lender|supplier).{0,30}(no\s+liability|not\s+liable|not\s+responsible|exempt\s+from).{0,30}(defect|quality|damage|loss)",
            "act": "Consumer Affairs Authority Act",
            "section": "31",
            "rule": "Suppliers are liable for defective products and cannot exclude liability for harm.",
            "recommendation": "POTENTIALLY ILLEGAL: Sellers cannot exclude all liability for defects."
        },
        {
            "pattern": r"(penalty|penalty\s+interest|late\s+fee).{0,30}(exceed|more\s+than).{0,20}(50|100|200)\s*%",
            "act": "Money Lending Ordinance",
            "section": "10",
            "rule": "Excessive penalty charges are unconscionable and may be set aside by court.",
            "recommendation": "ILLEGAL: Excessive penalty charges are unconscionable under Section 10."
        },
        {
            "pattern": r"(lender|creditor|pawnbroker).{0,30}(seize|confiscate|take\s+possession|forfeit).{0,30}(without\s+notice|without\s+court|immediately)",
            "act": "Pawnbrokers Ordinance",
            "section": "15",
            "rule": "Pawnbrokers must follow proper procedures before forfeiting pledges.",
            "recommendation": "ILLEGAL: Seizure or forfeiture requires proper notice and procedures under Section 15."
        },
        {
            "pattern": r"(default|defaulting).{0,30}(automatic|immediate).{0,30}(repossession|seizure|forfeiture|acceleration)",
            "act": "Consumer Credit Act",
            "section": "11",
            "rule": "Hire-purchase and credit agreements require proper notice before repossession.",
            "recommendation": "POTENTIALLY ILLEGAL: Automatic repossession without notice may violate Section 11."
        },
        {
            "pattern": r"(goods|product).{0,30}(sold\s+as\s+is|no\s+warranty|as-is\s+condition|with\s+all\s+faults)",
            "act": "Sale of Goods Ordinance",
            "section": "14",
            "rule": "Goods sold must be of merchantable quality unless defects specifically drawn to buyer's attention.",
            "recommendation": "REVIEW: 'As-is' clauses may not exclude statutory warranties under Section 14."
        },
        {
            "pattern": r"(refund|return|replacement).{0,30}(not\s+permitted|not\s+allowed|prohibited|no\s+refund|under\s+no\s+circumstances)",
            "act": "Consumer Affairs Authority Act",
            "section": "18",
            "rule": "Unfair trade practices including refusing legitimate refunds are prohibited.",
            "recommendation": "REVIEW: No-refund policies may violate consumer rights for defective goods."
        },
        {
            "pattern": r"(false|misleading|deceptive).{0,30}(representation|statement|claim|advertisement)",
            "act": "Consumer Affairs Authority Act",
            "section": "18",
            "rule": "False or misleading representations about goods or services are prohibited.",
            "recommendation": "ILLEGAL: False or misleading representations violate Section 18."
        },
        {
            "pattern": r"(early\s+settlement|prepayment|early\s+repayment).{0,30}(not\s+permitted|prohibited|penalty|fee\s+equal|full\s+interest)",
            "act": "Consumer Credit Act",
            "section": "9",
            "rule": "Borrowers have the right to early settlement with appropriate rebate on charges.",
            "recommendation": "REVIEW: Unreasonable restrictions on early settlement may violate Section 9."
        },
        {
            "pattern": r"(microfinance|micro\s+finance|mfi).{0,30}(not\s+licensed|unlicensed|unregistered)",
            "act": "Microfinance Act",
            "section": "24",
            "rule": "Microfinance institutions must be licensed to operate legally.",
            "recommendation": "ILLEGAL: Unlicensed microfinance operations violate Section 24."
        },
        {
            "pattern": r"(electronic\s+signature|e-signature|digital\s+signature).{0,30}(not\s+valid|invalid|unenforceable)",
            "act": "Electronic Transactions Act",
            "section": "4",
            "rule": "Electronic signatures are valid and enforceable under certain conditions.",
            "recommendation": "REVIEW: Electronic signatures may be valid under Section 4."
        },
    ],

    # ========== SALE OF GOODS DOMAIN ==========
    "sale_of_goods": [
        {
            "pattern": r"(seller|vendor).{0,30}(no\s+liability|not\s+liable|not\s+responsible).{0,30}(defect|quality|fitness|merchantable)",
            "act": "Sale of Goods Ordinance, No. 11 of 1896",
            "section": "14",
            "rule": "Implied condition that goods are of merchantable quality cannot be excluded.",
            "recommendation": "ILLEGAL: Excluding liability for merchantable quality violates Section 14 of the Sale of Goods Ordinance."
        },
        {
            "pattern": r"(buyer|purchaser).{0,30}(waive|waives|forfeit).{0,30}(right|rights).{0,30}(inspect|examination|reject)",
            "act": "Sale of Goods Ordinance, No. 11 of 1896",
            "section": "34",
            "rule": "Buyer has the right to examine goods before acceptance.",
            "recommendation": "ILLEGAL: Buyer's right to inspect goods before acceptance cannot be waived under Section 34."
        },
        {
            "pattern": r"(no\s+return|no\s+refund|all\s+sales?\s+final|non.?refundable).{0,30}(defect|faulty|not\s+as\s+described)",
            "act": "Sale of Goods Ordinance, No. 11 of 1896",
            "section": "13",
            "rule": "Buyer has the right to reject goods not matching description or sample.",
            "recommendation": "ILLEGAL: 'No return' clauses for defective goods violate Section 13."
        },
        {
            "pattern": r"(seller|vendor).{0,30}(substitute|replace\s+with\s+different|change\s+specifications).{0,30}(without\s+consent|unilaterally)",
            "act": "Sale of Goods Ordinance, No. 11 of 1896",
            "section": "13",
            "rule": "Goods must correspond with description; unilateral changes are unlawful.",
            "recommendation": "ILLEGAL: Unilateral substitution of goods violates Section 13."
        },
        {
            "pattern": r"(risk|loss|damage).{0,30}(pass|transfer).{0,30}(before\s+delivery|before\s+possession|irrespective\s+of\s+delivery)",
            "act": "Sale of Goods Ordinance, No. 11 of 1896",
            "section": "20",
            "rule": "Risk passes with property unless otherwise agreed, but buyer must have opportunity to inspect.",
            "recommendation": "REVIEW: Risk transfer before delivery may be unfair under Section 20."
        },
    ],

    # ========== MICROFINANCE / LENDING DOMAIN ==========
    "microfinance": [
        {
            "pattern": r"(interest|rate).{0,30}(compound|compounded|capitalize|capitalized).{0,30}(monthly|daily|weekly)",
            "act": "Money Lending Ordinance, No. 2 of 1918",
            "section": "10",
            "rule": "Compound interest clauses may be unenforceable if they lead to excessive charges.",
            "recommendation": "ILLEGAL: Compound interest clauses violate Section 10 of the Money Lending Ordinance."
        },
        {
            "pattern": r"(borrower|debtor).{0,30}(waive|waives|forfeit).{0,30}(right|rights).{0,30}(court|tribunal|legal)",
            "act": "Money Lending Ordinance, No. 2 of 1918",
            "section": "15",
            "rule": "Borrowers cannot be required to waive their legal rights.",
            "recommendation": "ILLEGAL: Requiring borrowers to waive legal rights violates Section 15."
        },
        {
            "pattern": r"(lender|creditor).{0,30}(harass|intimidat|threaten|coerce|force).{0,30}(borrower|debtor|family|property)",
            "act": "Money Lending Ordinance, No. 2 of 1918",
            "section": "15",
            "rule": "Harassment or intimidation of borrowers is prohibited.",
            "recommendation": "ILLEGAL: Harassment of borrowers violates Section 15 of the Money Lending Ordinance."
        },
        {
            "pattern": r"(loan|principal).{0,30}(not\s+in\s+writing|oral|verbal\s+agreement)",
            "act": "Money Lending Ordinance, No. 2 of 1918",
            "section": "3",
            "rule": "Loan agreements must be in writing stating principal, interest, and terms.",
            "recommendation": "ILLEGAL: Loan agreements must be in writing under Section 3."
        },
        {
            "pattern": r"(interest).{0,40}(exceed|above|over|more\s+than).{0,20}(lawful|legal|statutory|prescribed).{0,10}(limit|rate|maximum)",
            "act": "Money Lending Ordinance, No. 2 of 1918",
            "section": "10",
            "rule": "Interest exceeding legal limits may be unenforceable.",
            "recommendation": "ILLEGAL: Interest rates exceeding legal limits violate Section 10."
        },
        {
            "pattern": r"(microfinance|mfi|lending\s+institution).{0,30}(not\s+licensed|unlicensed|unregistered)",
            "act": "Microfinance Act No. 6 of 2016",
            "section": "24",
            "rule": "Microfinance institutions must be licensed.",
            "recommendation": "ILLEGAL: Operating without license violates Section 24 of the Microfinance Act."
        },
    ],

    # ========== PAWN / PLEDGE DOMAIN ==========
    "pawn_pledge": [
        {
            "pattern": r"(pawnbroker|pawn\s+shop).{0,30}(not\s+licensed|unlicensed|without\s+license)",
            "act": "Pawnbrokers Ordinance",
            "section": "3",
            "rule": "Pawnbrokers must be licensed to operate.",
            "recommendation": "ILLEGAL: Operating as a pawnbroker without license violates Section 3."
        },
        {
            "pattern": r"(no\s+receipt|without\s+receipt|receipt\s+not\s+required|no\s+pawn\s+ticket)",
            "act": "Pawnbrokers Ordinance",
            "section": "15",
            "rule": "Pawnbroker must issue a pawn ticket/receipt for every pledge.",
            "recommendation": "ILLEGAL: Failure to issue pawn ticket violates Section 15."
        },
        {
            "pattern": r"(pledged\s+item|pawn).{0,30}(forfeit|forfeited|dispose|disposed|sold).{0,30}(without\s+notice|immediately|before\s+expiry)",
            "act": "Pawnbrokers Ordinance",
            "section": "15",
            "rule": "Pledged items cannot be disposed of before the redemption period expires.",
            "recommendation": "ILLEGAL: Disposing of pledged items before redemption period expires violates Section 15."
        },
        {
            "pattern": r"(pawnbroker).{0,30}(charge|fee|interest).{0,30}(exceed|above|excessive|unreasonable)",
            "act": "Pawnbrokers Ordinance",
            "section": "General",
            "rule": "Pawnbrokers must charge within prescribed limits.",
            "recommendation": "ILLEGAL: Excessive charges violate the Pawnbrokers Ordinance."
        },
    ],

    # ========== PROPERTY / LAND SALE DOMAIN ==========
    "land_property": [
        {
            "pattern": r"(sale|transfer|conveyance).{0,30}(land|property|immovable).{0,30}(oral|verbal|not\s+in\s+writing|without\s+notary)",
            "act": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "section": "2",
            "rule": "No sale or transfer of land is valid unless in writing, signed, and attested by a notary.",
            "recommendation": "ILLEGAL: Land transfers must be in writing and attested by a notary under Section 2."
        },
        {
            "pattern": r"(deed|transfer).{0,30}(not\s+registered|need\s+not\s+be\s+registered|registration\s+not\s+required)",
            "act": "Registration of Documents Ordinance",
            "section": "2",
            "rule": "Every deed affecting land must be registered.",
            "recommendation": "ILLEGAL: Deeds affecting land must be registered under Section 2."
        },
        {
            "pattern": r"(buyer|purchaser|vendee).{0,30}(waive|waives).{0,30}(title\s+search|title\s+verification|encumbrance\s+check)",
            "act": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "section": "2",
            "rule": "Buyer should verify title and encumbrances before purchase.",
            "recommendation": "REVIEW: Waiving title verification is risky and may lead to disputes."
        },
        {
            "pattern": r"(vendor|seller).{0,30}(no\s+warranty|not\s+warrant|as\s+is).{0,30}(title|ownership|encumbrance)",
            "act": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "section": "2",
            "rule": "Vendor must warrant good and marketable title.",
            "recommendation": "ILLEGAL: Vendor must provide warranty of title in land transactions."
        },
    ],

    # ========== ELECTRONIC CONTRACT / E-COMMERCE DOMAIN ==========
    "electronic_contract": [
        {
            "pattern": r"(electronic\s+contract|online\s+agreement|e-commerce).{0,30}(not\s+valid|not\s+enforceable|invalid|void)",
            "act": "Electronic Transactions Act, No. 19 of 2006",
            "section": "4",
            "rule": "Electronic contracts are valid and enforceable when conditions are met.",
            "recommendation": "REVIEW: Electronic contracts are valid under Section 4 of the Electronic Transactions Act."
        },
        {
            "pattern": r"(electronic\s+signature|e-signature).{0,30}(not\s+acceptable|invalid|rejected|not\s+recognized)",
            "act": "Electronic Transactions Act, No. 19 of 2006",
            "section": "7",
            "rule": "Electronic signatures satisfy legal signature requirements if reliable.",
            "recommendation": "REVIEW: Electronic signatures are valid under Section 7."
        },
        {
            "pattern": r"(website|platform|service\s+provider).{0,30}(no\s+liability|not\s+liable|not\s+responsible).{0,30}(any|all|whatsoever)",
            "act": "Electronic Transactions Act, No. 19 of 2006",
            "section": "General",
            "rule": "Blanket liability exclusions may be unfair in e-commerce contexts.",
            "recommendation": "REVIEW: Blanket liability exclusions may be unenforceable."
        },
        {
            "pattern": r"(terms|conditions).{0,30}(change|modify|amend).{0,30}(without\s+notice|any\s+time|unilaterally)",
            "act": "Electronic Transactions Act, No. 19 of 2006",
            "section": "General",
            "rule": "Changes to terms must be communicated to users; unilateral changes may be void.",
            "recommendation": "ILLEGAL: Unilateral changes to terms without notice may violate fair dealing principles."
        },
    ],
}


# ==============================
# STEP 4: LEGAL Clause Patterns
# ==============================
LEGAL_PATTERNS = {
    "employment": [
        {
            "pattern": r"(working\s+hours?|hours\s+of\s+work).{0,50}(not\s+exceed|shall\s+be|maximum).{0,20}(8|eight)\s+hours?",
            "act": "Shop and Office Employees Act",
            "section": "3(1)",
            "rule": "Working hours shall not exceed 8 hours per day excluding intervals for rest and meals.",
            "recommendation": "COMPLIANT: Daily working hours of 8 hours complies with Section 3(1)."
        },
        {
            "pattern": r"(45|forty.?five)\s+hours?.{0,20}(week|weekly)",
            "act": "Shop and Office Employees Act",
            "section": "3(1)",
            "rule": "Working hours shall not exceed 45 hours per week.",
            "recommendation": "COMPLIANT: Weekly 45 hours limit complies with Section 3(1)."
        },
        {
            "pattern": r"(overtime|extra\s+hours?).{0,30}(1\.5|one\s+and\s+a\s+half|150\s*%|time\s+and\s+a\s+half)",
            "act": "Shop and Office Employees Act",
            "section": "4",
            "rule": "Overtime work shall be compensated at 1.5 times the normal wage rate.",
            "recommendation": "COMPLIANT: Overtime at 1.5x rate complies with Section 4."
        },
        {
            "pattern": r"(epf|employees?.{0,10}provident\s+fund).{0,30}(12|twelve)\s*%",
            "act": "Employees' Provident Fund Act",
            "section": "8",
            "rule": "Employer shall contribute 12% and deduct 8% from employee earnings to EPF.",
            "recommendation": "COMPLIANT: EPF 12% employer contribution complies with Section 8."
        },
        {
            "pattern": r"(epf|provident\s+fund).{0,30}(8|eight)\s*%.{0,20}(employee|deduct)",
            "act": "Employees' Provident Fund Act",
            "section": "8",
            "rule": "Employee contribution of 8% shall be deducted from earnings.",
            "recommendation": "COMPLIANT: EPF 8% employee deduction complies with Section 8."
        },
        {
            "pattern": r"(etf|employees?.{0,10}trust\s+fund).{0,30}(3|three)\s*%",
            "act": "Employees' Trust Fund Act",
            "section": "2",
            "rule": "Employer shall contribute 3% of employee total earnings to ETF.",
            "recommendation": "COMPLIANT: ETF 3% employer contribution complies with Section 2."
        },
        {
            "pattern": r"(gratuity|payment\s+of\s+gratuity).{0,30}(5|five)\s+years?.{0,20}(service|employment)",
            "act": "Payment of Gratuity Act",
            "section": "2(1)",
            "rule": "Employees with 5+ years of service are entitled to gratuity of half month's wages per year.",
            "recommendation": "COMPLIANT: Gratuity provision after 5 years complies with Section 2(1)."
        },
        {
            "pattern": r"(annual\s+leave|vacation\s+leave).{0,30}(14|fourteen)\s+days?",
            "act": "Shop and Office Employees Act",
            "section": "6(1)",
            "rule": "Employees are entitled to 14 days annual leave per year.",
            "recommendation": "COMPLIANT: 14 days annual leave complies with Section 6(1)."
        },
        {
            "pattern": r"(casual\s+leave|sick\s+leave|medical\s+leave).{0,30}(7|seven)\s+days?",
            "act": "Shop and Office Employees Act",
            "section": "6(3)",
            "rule": "Employees are entitled to 7 days casual leave and 7 days sick leave per year.",
            "recommendation": "COMPLIANT: 7 days leave entitlement complies with Section 6(3)."
        },
        {
            "pattern": r"(maternity\s+leave|maternity\s+benefits).{0,30}(84|eighty.?four)\s+(days?|working\s+days?)",
            "act": "Maternity Benefits Ordinance",
            "section": "2",
            "rule": "Female employees are entitled to 84 working days paid maternity leave.",
            "recommendation": "COMPLIANT: 84 days maternity leave complies with Section 2."
        },
        {
            "pattern": r"(public\s+holiday|poya\s+day|government\s+holiday).{0,30}(entitled|paid|compensation|double\s+pay)",
            "act": "Shop and Office Employees Act",
            "section": "7(1)",
            "rule": "Employees must be given paid public holidays or double pay in lieu.",
            "recommendation": "COMPLIANT: Public holiday entitlement complies with Section 7(1)."
        },
        {
            "pattern": r"(termination|terminate).{0,30}(one|1)\s+month.{0,20}(notice|written\s+notice)",
            "act": "Termination of Employment of Workmen Act",
            "section": "2(1)",
            "rule": "Termination requires reasonable notice; employer must provide written reasons if requested.",
            "recommendation": "COMPLIANT: One month notice period is reasonable."
        },
        {
            "pattern": r"(termination|dismiss).{0,30}(written\s+reasons?|reasons?\s+in\s+writing).{0,30}(14|fourteen)\s+days?",
            "act": "Termination of Employment of Workmen Act",
            "section": "2(4)",
            "rule": "Employer must provide written reasons for termination within 14 days of request.",
            "recommendation": "COMPLIANT: Provision for written reasons complies with Section 2(4)."
        },
        {
            "pattern": r"(probation|probationary).{0,30}(3|three|6|six)\s+months?",
            "act": "Termination of Employment of Workmen Act / Industrial Disputes Act",
            "section": "2(1) / 31B",
            "rule": "Probation periods are permitted but termination during probation may still be challengeable if employee is a 'workman'.",
            "recommendation": "NOTE: Probation period of 3-6 months is standard. However, probation does NOT grant unlimited termination rights - see Industrial Disputes Act Section 31B."
        },
        {
            "pattern": r"(dispute|grievance).{0,30}(labour\s+tribunal|commissioner\s+of\s+labour|industrial\s+court)",
            "act": "Industrial Disputes Act",
            "section": "31B(1)(a)",
            "rule": "Employees have the right to refer disputes to labour tribunals.",
            "recommendation": "COMPLIANT: Reference to dispute resolution mechanisms complies with Section 31B(1)(a)."
        },
        {
            "pattern": r"(minimum\s+wage|national\s+minimum).{0,30}(as\s+prescribed|statutory|legal|national)",
            "act": "National Minimum Wage of Workers Act",
            "section": "3",
            "rule": "Wages shall not be less than the national minimum wage as prescribed.",
            "recommendation": "COMPLIANT: Reference to national minimum wage complies with Section 3."
        },
        {
            "pattern": r"(wages?|salary).{0,30}(paid|payment).{0,30}(monthly|every\s+month|regular\s+intervals)",
            "act": "Wages Boards Ordinance",
            "section": "17",
            "rule": "Wages must be paid at regular intervals not exceeding one month.",
            "recommendation": "COMPLIANT: Monthly wage payment complies with Section 17."
        },
        {
            "pattern": r"(return|surrender).{0,30}(company\s+property|equipment|materials|id\s+card)",
            "act": "Prevention of Frauds Ordinance",
            "section": "General",
            "rule": "Employees must return company property upon termination.",
            "recommendation": "COMPLIANT: Standard and lawful clause."
        },
        {
            "pattern": r"(confidential|confidentiality).{0,30}(proprietary|trade\s+secret|business\s+information)",
            "act": "Prevention of Frauds Ordinance",
            "section": "2",
            "rule": "Confidentiality clauses must be in writing and reasonable in scope.",
            "recommendation": "COMPLIANT: Standard confidentiality clause."
        },
        {
            "pattern": r"(intellectual\s+property|inventions?|designs?).{0,30}(belong|owned|ownership).{0,20}(employer)",
            "act": "Intellectual Property Act",
            "section": "General",
            "rule": "Work-for-hire intellectual property typically belongs to employer.",
            "recommendation": "COMPLIANT: Standard IP assignment clause."
        },
        {
            "pattern": r"(amendment|modify).{0,30}(writing|written).{0,30}(signed|both\s+parties)",
            "act": "Prevention of Frauds Ordinance",
            "section": "2",
            "rule": "Contract amendments should be in writing and signed by both parties.",
            "recommendation": "COMPLIANT: Written amendments comply with Section 2."
        },
        {
            "pattern": r"(salary|wage|remuneration).{0,30}(lkr|rupees).{0,30}(monthly|per\s+month)",
            "act": "Wages Boards Ordinance",
            "section": "17",
            "rule": "Wages must be clearly specified and paid at agreed intervals.",
            "recommendation": "COMPLIANT: Clear salary specification complies with Section 17."
        },
        {
            "pattern": r"(termination|terminate).{0,30}(misconduct|gross\s+misconduct).{0,30}(proper\s+investigation|investigation|inquiry|documented)",
            "act": "Termination of Employment of Workmen Act",
            "section": "2(5)",
            "rule": "Disciplinary termination requires proper investigation and written reasons.",
            "recommendation": "COMPLIANT: Termination for misconduct with proper process complies with Section 2(5)."
        },
        {
            "pattern": r"(young\s+person|minor|under\s+18).{0,30}(restricted|prohibited|special\s+conditions)",
            "act": "Employment of Women, Young Persons and Children Act",
            "section": "13",
            "rule": "Employment of young persons under 18 is subject to restrictions.",
            "recommendation": "COMPLIANT: Recognition of youth employment restrictions complies with Section 13."
        },
    ],
    "rental": [
        {
            "pattern": r"(rent|rental|monthly\s+rent).{0,30}(lkr|rupees|rs\.?).{0,30}(monthly|per\s+month|month)",
            "act": "Rent Act",
            "section": "3",
            "rule": "Standard rent shall be the rent agreed upon between landlord and tenant.",
            "recommendation": "COMPLIANT: Clear rent specification complies with Section 3."
        },
        {
            "pattern": r"(rent|rental).{0,20}(amount|payable|agreed|standard\s+rent)",
            "act": "Rent Act",
            "section": "3",
            "rule": "The standard rent is as agreed between the parties.",
            "recommendation": "COMPLIANT: Rent amount properly specified under Section 3."
        },
        {
            "pattern": r"(advance\s+rent|rent\s+in\s+advance|advance).{0,30}(1|one|2|two|3|three)\s+months?",
            "act": "Rent Act",
            "section": "9(1)(a)",
            "rule": "Advance rent shall not exceed 3 months of standard rent.",
            "recommendation": "COMPLIANT: Advance rent within 3 months limit complies with Section 9(1)(a)."
        },
        {
            "pattern": r"(security\s+deposit|deposit|refundable\s+deposit).{0,30}(refund|refundable|return|returned|end\s+of\s+tenancy)",
            "act": "Rent Act",
            "section": "9",
            "rule": "Deposits are refundable subject to deductions for damages.",
            "recommendation": "COMPLIANT: Refundable deposit provision complies with Section 9."
        },
        {
            "pattern": r"(notice|written\s+notice).{0,30}(1|one|2|two|3|three)\s+months?.{0,20}(vacate|terminate|end)",
            "act": "Rent Act",
            "section": "22",
            "rule": "Proper notice must be given before termination proceedings.",
            "recommendation": "COMPLIANT: Reasonable notice period complies with Section 22."
        },
        {
            "pattern": r"(tenant|lessee).{0,30}(maintain|maintenance|keep|good\s+condition|proper\s+condition|day.?to.?day)",
            "act": "Rent Act",
            "section": "16",
            "rule": "Tenant shall keep premises in good condition and maintain day-to-day repairs.",
            "recommendation": "COMPLIANT: Tenant maintenance obligations comply with Section 16."
        },
        {
            "pattern": r"(landlord|lessor).{0,30}(responsible|shall\s+maintain|obligation).{0,30}(structural|major\s+repairs|roof|walls|foundation)",
            "act": "Rent Act",
            "section": "16",
            "rule": "Landlord shall keep premises in good tenantable repair including structural repairs.",
            "recommendation": "COMPLIANT: Landlord structural repair responsibility complies with Section 16."
        },
        {
            "pattern": r"(landlord|lessor).{0,30}(provide|supply|maintain).{0,30}(water|electricity|essential\s+services)",
            "act": "Rent Act",
            "section": "17",
            "rule": "Landlord must provide and maintain essential services.",
            "recommendation": "COMPLIANT: Essential services provision complies with Section 17."
        },
        {
            "pattern": r"(lease|tenancy).{0,20}(term|period|duration).{0,30}(year|month|years|months)",
            "act": "Rent Act",
            "section": "2",
            "rule": "Tenancy term should be clearly specified.",
            "recommendation": "COMPLIANT: Clear lease term specified."
        },
        {
            "pattern": r"(premises|property).{0,30}(residential|dwelling|living)\s+purpose",
            "act": "Rent Act",
            "section": "2",
            "rule": "The purpose of use should be specified in the agreement.",
            "recommendation": "COMPLIANT: Clear purpose specification."
        },
        {
            "pattern": r"(tenant|lessee).{0,30}(shall\s+not|prohibited).{0,30}(subletting|sub-let).{0,20}(without\s+consent|prior\s+approval|written\s+consent)",
            "act": "Rent Act",
            "section": "10",
            "rule": "Subletting requires landlord consent.",
            "recommendation": "COMPLIANT: Subletting clause with consent provision complies with Section 10."
        },
        {
            "pattern": r"(tenancy|lease|agreement).{0,30}(commence|start|begin).{0,30}(day|date|january|february|march|april|may|june|july|august|september|october|november|december)",
            "act": "Rent Act",
            "section": "2",
            "rule": "Commencement date should be clearly specified.",
            "recommendation": "COMPLIANT: Clear commencement date specified."
        },
        {
            "pattern": r"(two|2|three|3|one|1)\s*(years?|months?).{0,20}(term|period|duration|tenancy)",
            "act": "Rent Act",
            "section": "2",
            "rule": "Fixed term tenancies are recognized.",
            "recommendation": "COMPLIANT: Fixed lease term properly specified."
        },
        {
            "pattern": r"(mutual|mutually).{0,20}(agree|agreed|consent|written).{0,20}(extend|renew|terminate)",
            "act": "Rent Act",
            "section": "General",
            "rule": "Mutual agreement provisions are standard and lawful.",
            "recommendation": "COMPLIANT: Mutual agreement clause is reasonable."
        },
        {
            "pattern": r"(lease|agreement).{0,30}(registered|registration).{0,30}(exceed|over|more\s+than).{0,20}(one|1)\s+year",
            "act": "Registration of Documents Ordinance",
            "section": "2",
            "rule": "Leases exceeding one year should be registered.",
            "recommendation": "COMPLIANT: Registration requirement for leases over 1 year recognized."
        },
        {
            "pattern": r"(rent\s+receipt|receipt\s+for\s+rent|acknowledge\s+payment)",
            "act": "Rent Act",
            "section": "33",
            "rule": "Landlord must provide receipt for rent payments when requested.",
            "recommendation": "COMPLIANT: Rent receipt provision complies with Section 33."
        },
        {
            "pattern": r"(eviction|eject|possession).{0,30}(court\s+order|valid\s+grounds|section\s+22|non-payment|breach)",
            "act": "Rent Act",
            "section": "22(1)",
            "rule": "Eviction requires court order and valid grounds under Section 22.",
            "recommendation": "COMPLIANT: Eviction clause references proper legal grounds under Section 22(1)."
        },
    ],
    "finance_leasing": [
        {
            "pattern": r"(lease\s+term|lease\s+period|lease\s+shall\s+commence).{0,40}(five|5)\s+(years?|year).{0,20}(unless\s+terminated|period|term)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "3",
            "rule": "Finance lease term and commencement date must be clearly specified in writing.",
            "recommendation": "COMPLIANT: Lease term of 5 years is clearly specified as required by the Finance Leasing Act."
        },
        {
            "pattern": r"(lease\s+rental|lease\s+rentals|monthly\s+lease).{0,30}(lkr|rupees|rs).{0,20}(\d+)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "3",
            "rule": "Lease rental amounts must be clearly specified in writing.",
            "recommendation": "COMPLIANT: Monthly lease rental amount is clearly specified as required."
        },
        {
            "pattern": r"(payment|lease\s+payment).{0,30}(bank\s+transfer|cheque|cash).{0,20}(designated|specified|account)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "3",
            "rule": "Payment method and terms should be clearly specified.",
            "recommendation": "COMPLIANT: Payment method and account details are specified."
        },
        {
            "pattern": r"(lessee\s+shall).{0,30}(maintain|maintenance|care|proper\s+use|properly\s+use).{0,30}(vehicle|equipment|leased)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "12",
            "rule": "The lessee must care for and properly use the leased equipment.",
            "recommendation": "COMPLIANT: Lessee's maintenance obligations comply with Section 12."
        },
        {
            "pattern": r"(lessee\s+shall).{0,30}(insure|insurance).{0,30}(comprehensive|vehicle|equipment)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "12",
            "rule": "Insurance requirements for leased assets are standard and lawful.",
            "recommendation": "COMPLIANT: Insurance requirement for leased vehicle/equipment is reasonable and complies with Section 12."
        },
        {
            "pattern": r"(govern|governed\s+by).{0,30}(laws?\s+of\s+sri\s+lanka|sri\s+lankan\s+law)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "General",
            "rule": "Finance leasing agreements in Sri Lanka are governed by the Finance Leasing Act.",
            "recommendation": "COMPLIANT: Governing law clause is standard and appropriate."
        },
        {
            "pattern": r"(entire\s+agreement|entire\s+understanding).{0,30}(supersedes|prior\s+discussions|representations)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "General",
            "rule": "Entire agreement clauses are standard contract provisions.",
            "recommendation": "COMPLIANT: Standard entire agreement clause."
        },
        {
            "pattern": r"(lessor\s+may).{0,30}(demand|accelerate|end\s+the\s+lease|reclaim).{0,30}(default|breach)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "20",
            "rule": "If the lessee defaults, the lessor can demand full payment, end the lease, reclaim equipment, and seek damages.",
            "recommendation": "COMPLIANT: Default remedies clause complies with Section 20 of the Finance Leasing Act."
        },
        {
            "pattern": r"(written\s+notice|notice\s+in\s+writing).{0,30}(default|breach).{0,30}(timeline|time\s+to\s+fix|remedy|cure)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "21(1)",
            "rule": "Before enforcing default rights, the lessor must serve written notice specifying the default and timeline to remedy.",
            "recommendation": "COMPLIANT: Written notice requirement for default complies with Section 21(1)."
        },
        {
            "pattern": r"(peaceful\s+possession|quiet\s+possession|right\s+to\s+possession).{0,30}(leased|equipment|vehicle)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "11(1)",
            "rule": "The lessee has a right to peaceful possession of leased equipment; the lessor must protect it.",
            "recommendation": "COMPLIANT: Recognition of lessee's right to quiet possession complies with Section 11(1)."
        },
        {
            "pattern": r"(end\s+of|upon\s+termination|at\s+the\s+end).{0,30}(lease|term).{0,30}(return|surrender).{0,30}(equipment|vehicle)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "15",
            "rule": "At the end of the lease, the lessee must return the equipment unless ownership was agreed.",
            "recommendation": "COMPLIANT: Equipment return clause complies with Section 15."
        },
        {
            "pattern": r"(registered|registration).{0,30}(finance\s+leasing|leasing\s+company|financial\s+institution)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "2",
            "rule": "A person must be registered to legally run a finance leasing business.",
            "recommendation": "COMPLIANT: Reference to registered finance leasing business complies with Section 2."
        },
        {
            "pattern": r"(60|sixty)\s+(consecutive\s+)?months",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "3",
            "rule": "Lease period clearly specified.",
            "recommendation": "COMPLIANT: Lease period of 60 months is clearly stated."
        },
        {
            "pattern": r"(on\s+or\s+before).{0,20}(\d+)(st|nd|rd|th)?\s+day.{0,20}(each\s+month|monthly)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "3",
            "rule": "Payment due date clearly specified.",
            "recommendation": "COMPLIANT: Monthly payment due date is clearly specified."
        },
        {
            "pattern": r"(lessee\s+shall\s+not).{0,30}(assign|transfer).{0,30}(without|prior).{0,20}(consent|approval)",
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "3",
            "rule": "Assignment restrictions with consent requirement are standard.",
            "recommendation": "COMPLIANT: Assignment restriction with lessor consent is reasonable."
        },
    ],
    "consumer": [
        {
            "pattern": r"(interest\s+rate|rate\s+of\s+interest|interest).{0,30}(per\s+annum|annual|p\.a\.|\%|percent)",
            "act": "Money Lending Ordinance",
            "section": "3",
            "rule": "Loan agreement must state interest rate clearly in writing.",
            "recommendation": "COMPLIANT: Interest rate properly disclosed under Section 3."
        },
        {
            "pattern": r"(interest).{0,20}(\d+(\.\d+)?\s*(%|percent|per\s+cent)).{0,20}(simple\s+interest|per\s+annum)",
            "act": "Money Lending Ordinance",
            "section": "3",
            "rule": "Interest rate and calculation method must be specified.",
            "recommendation": "COMPLIANT: Interest rate clearly stated as required by Section 3."
        },
        {
            "pattern": r"(loan|principal).{0,20}(amount|sum).{0,20}(lkr|rupees|rs)",
            "act": "Money Lending Ordinance",
            "section": "3",
            "rule": "Principal amount must be stated in writing.",
            "recommendation": "COMPLIANT: Loan amount clearly stated as required by Section 3."
        },
        {
            "pattern": r"(repayment|installment|emi|monthly\s+payment).{0,30}(schedule|monthly|payment|plan)",
            "act": "Consumer Credit Act",
            "section": "6",
            "rule": "Repayment terms and schedule must be specified in writing.",
            "recommendation": "COMPLIANT: Clear repayment schedule complies with Section 6."
        },
        {
            "pattern": r"(total\s+amount|total\s+price|total\s+payable).{0,30}(lkr|rupees|disclosed|stated)",
            "act": "Consumer Credit Act",
            "section": "3",
            "rule": "Total amount payable must be disclosed before agreement.",
            "recommendation": "COMPLIANT: Total amount disclosure complies with Section 3."
        },
        {
            "pattern": r"(borrower|buyer|consumer).{0,30}(right|entitled).{0,30}(prepay|early\s+repayment|early\s+settlement|pay\s+off)",
            "act": "Consumer Credit Act",
            "section": "9",
            "rule": "Borrower has the right to early settlement with appropriate rebate.",
            "recommendation": "COMPLIANT: Early settlement right complies with Section 9."
        },
        {
            "pattern": r"(cooling\s+off|cancellation|withdrawal).{0,20}(period|right).{0,20}(\d+\s+days?)",
            "act": "Consumer Credit Act",
            "section": "5",
            "rule": "Consumer has right to cancel within cooling-off period.",
            "recommendation": "COMPLIANT: Cooling-off period complies with Section 5."
        },
        {
            "pattern": r"(full\s+disclosure|disclosure).{0,30}(fees|charges|costs|terms|apr|total\s+cost)",
            "act": "Consumer Credit Act",
            "section": "3",
            "rule": "Full disclosure of all fees and charges is required.",
            "recommendation": "COMPLIANT: Proper disclosure of terms complies with Section 3."
        },
        {
            "pattern": r"(warranty|guarantee).{0,30}(defect|repair|replace|period|manufacturer)",
            "act": "Sale of Goods Ordinance",
            "section": "15",
            "rule": "Implied warranty of fitness for purpose applies to goods.",
            "recommendation": "COMPLIANT: Warranty provision complies with Section 15."
        },
        {
            "pattern": r"(goods|product).{0,30}(merchantable\s+quality|fit\s+for\s+purpose|reasonably\s+fit)",
            "act": "Sale of Goods Ordinance",
            "section": "14",
            "rule": "Goods must be of merchantable quality.",
            "recommendation": "COMPLIANT: Quality standard complies with Section 14."
        },
        {
            "pattern": r"(seller|vendor).{0,30}(title|ownership|right\s+to\s+sell|free\s+from\s+encumbrance)",
            "act": "Sale of Goods Ordinance",
            "section": "13",
            "rule": "Seller must have right to sell and goods free from encumbrances.",
            "recommendation": "COMPLIANT: Title warranty complies with Section 13."
        },
        {
            "pattern": r"(hire.?purchase|installment\s+sale).{0,30}(total\s+price|number\s+of\s+installments|right\s+to\s+terminate)",
            "act": "Consumer Credit Act",
            "section": "11",
            "rule": "Hire-purchase agreements must disclose total price and termination rights.",
            "recommendation": "COMPLIANT: Hire-purchase disclosure complies with Section 11."
        },
        {
            "pattern": r"(finance\s+lease|leasing).{0,30}(registered|agreement\s+in\s+writing|terms\s+disclosed)",
            "act": "Finance Leasing Act",
            "section": "3",
            "rule": "Finance lease agreements must be in writing and registered.",
            "recommendation": "COMPLIANT: Finance lease requirements comply with Section 3."
        },
        {
            "pattern": r"(pawn|pledge|security).{0,30}(receipt|redemption|proper\s+valuation)",
            "act": "Pawnbrokers Ordinance",
            "section": "15",
            "rule": "Pawnbroker must provide proper receipt and follow redemption procedures.",
            "recommendation": "COMPLIANT: Pawnbroking procedures comply with Section 15."
        },
        {
            "pattern": r"(electronic|digital|online).{0,30}(signature|contract|agreement|transaction)",
            "act": "Electronic Transactions Act",
            "section": "4",
            "rule": "Electronic contracts and signatures are valid and enforceable.",
            "recommendation": "COMPLIANT: Electronic transaction validity recognized under Section 4."
        },
        {
            "pattern": r"(partnership|partners).{0,30}(share|profit|management|participate|equal\s+rights)",
            "act": "Partnership Ordinance",
            "section": "28",
            "rule": "Partners have rights to share profits and participate in management.",
            "recommendation": "COMPLIANT: Partnership rights comply with Section 28."
        },
        {
            "pattern": r"(consumer\s+complaint|complaint\s+procedure|dispute\s+resolution|consumer\s+rights)",
            "act": "Consumer Affairs Authority Act",
            "section": "10",
            "rule": "Consumers have protection against unfair trade practices.",
            "recommendation": "COMPLIANT: Consumer rights acknowledgment complies with Section 10."
        },
    ],

    # ========== SALE OF GOODS DOMAIN ==========
    "sale_of_goods": [
        {
            "pattern": r"(goods|product).{0,30}(merchantable\s+quality|fit\s+for\s+purpose|reasonably\s+fit|free\s+from\s+defect)",
            "act": "Sale of Goods Ordinance, No. 11 of 1896",
            "section": "14",
            "rule": "Goods must be of merchantable quality.",
            "recommendation": "COMPLIANT: Merchantable quality provision complies with Section 14."
        },
        {
            "pattern": r"(seller|vendor).{0,30}(right\s+to\s+sell|title|ownership|free\s+from\s+encumbrance)",
            "act": "Sale of Goods Ordinance, No. 11 of 1896",
            "section": "13",
            "rule": "Seller must have the right to sell and goods free from encumbrances.",
            "recommendation": "COMPLIANT: Title warranty complies with Section 13."
        },
        {
            "pattern": r"(delivery|deliver).{0,30}(within|on\s+or\s+before|agreed\s+date|specified\s+date)",
            "act": "Sale of Goods Ordinance, No. 11 of 1896",
            "section": "27",
            "rule": "Delivery of goods and payment of price are concurrent conditions.",
            "recommendation": "COMPLIANT: Delivery terms properly specified under Section 27."
        },
        {
            "pattern": r"(buyer|purchaser).{0,30}(right\s+to\s+inspect|examine|inspection\s+before\s+acceptance)",
            "act": "Sale of Goods Ordinance, No. 11 of 1896",
            "section": "34",
            "rule": "Buyer has the right to examine goods before acceptance.",
            "recommendation": "COMPLIANT: Inspection rights recognized under Section 34."
        },
        {
            "pattern": r"(warranty|guarantee).{0,30}(defect|repair|replace|period|quality)",
            "act": "Sale of Goods Ordinance, No. 11 of 1896",
            "section": "15",
            "rule": "Implied warranty of fitness for purpose applies.",
            "recommendation": "COMPLIANT: Warranty provision complies with Section 15."
        },
        {
            "pattern": r"(price|consideration|purchase\s+price).{0,30}(lkr|rupees|rs|agreed|specified|amount)",
            "act": "Sale of Goods Ordinance, No. 11 of 1896",
            "section": "8",
            "rule": "Price must be specified or ascertainable.",
            "recommendation": "COMPLIANT: Price properly specified under Section 8."
        },
    ],

    # ========== MICROFINANCE / LENDING DOMAIN ==========
    "microfinance": [
        {
            "pattern": r"(interest\s+rate|rate\s+of\s+interest).{0,30}(per\s+annum|annual|p\.a\.|clearly\s+stated|\%|percent)",
            "act": "Money Lending Ordinance, No. 2 of 1918",
            "section": "3",
            "rule": "Interest rate must be clearly stated in writing.",
            "recommendation": "COMPLIANT: Interest rate properly disclosed under Section 3."
        },
        {
            "pattern": r"(loan|agreement).{0,30}(in\s+writing|written\s+agreement|signed|executed)",
            "act": "Money Lending Ordinance, No. 2 of 1918",
            "section": "3",
            "rule": "Loan agreements must be in writing.",
            "recommendation": "COMPLIANT: Written agreement complies with Section 3."
        },
        {
            "pattern": r"(principal|loan\s+amount).{0,30}(lkr|rupees|rs|stated|specified|amount)",
            "act": "Money Lending Ordinance, No. 2 of 1918",
            "section": "3",
            "rule": "Principal amount must be clearly stated.",
            "recommendation": "COMPLIANT: Principal amount properly stated under Section 3."
        },
        {
            "pattern": r"(repayment|installment).{0,30}(schedule|monthly|plan|due\s+date)",
            "act": "Money Lending Ordinance, No. 2 of 1918",
            "section": "General",
            "rule": "Repayment terms must be clearly specified.",
            "recommendation": "COMPLIANT: Repayment schedule properly specified."
        },
        {
            "pattern": r"(licensed|registered).{0,30}(microfinance|mfi|lender|lending\s+institution)",
            "act": "Microfinance Act No. 6 of 2016",
            "section": "24",
            "rule": "Microfinance institutions must be licensed.",
            "recommendation": "COMPLIANT: Licensed institution reference complies with Section 24."
        },
        {
            "pattern": r"(total\s+cost|total\s+amount|total\s+payable|all\s+fees).{0,30}(disclosed|stated|specified)",
            "act": "Money Lending Ordinance, No. 2 of 1918",
            "section": "3",
            "rule": "Total cost of borrowing must be disclosed.",
            "recommendation": "COMPLIANT: Total cost disclosure complies with Section 3."
        },
    ],

    # ========== PAWN / PLEDGE DOMAIN ==========
    "pawn_pledge": [
        {
            "pattern": r"(pawn\s+ticket|receipt|pawn\s+receipt).{0,30}(issue|provided|given|deliver)",
            "act": "Pawnbrokers Ordinance",
            "section": "15",
            "rule": "Pawnbroker must issue pawn ticket for every pledge.",
            "recommendation": "COMPLIANT: Pawn ticket issuance complies with Section 15."
        },
        {
            "pattern": r"(redemption|redeem).{0,30}(period|within|right|entitled)",
            "act": "Pawnbrokers Ordinance",
            "section": "15",
            "rule": "Pledger has the right to redeem within the specified period.",
            "recommendation": "COMPLIANT: Redemption rights properly recognized under Section 15."
        },
        {
            "pattern": r"(licensed|license|registered).{0,30}(pawnbroker|pawn\s+shop)",
            "act": "Pawnbrokers Ordinance",
            "section": "3",
            "rule": "Pawnbroker must be licensed to operate.",
            "recommendation": "COMPLIANT: Licensed pawnbroker reference complies with Section 3."
        },
        {
            "pattern": r"(valuation|appraisal|assessed).{0,30}(item|pledge|gold|jewelry|jewellery)",
            "act": "Pawnbrokers Ordinance",
            "section": "General",
            "rule": "Proper valuation of pledged items is required.",
            "recommendation": "COMPLIANT: Valuation provision complies with the Pawnbrokers Ordinance."
        },
    ],

    # ========== PROPERTY / LAND SALE DOMAIN ==========
    "land_property": [
        {
            "pattern": r"(deed|transfer|conveyance).{0,30}(notary|notarially\s+attested|notarial).{0,30}(witness|signed|attested)",
            "act": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "section": "2",
            "rule": "Land transfers must be in writing, attested by a notary and witnesses.",
            "recommendation": "COMPLIANT: Notarial attestation complies with Section 2."
        },
        {
            "pattern": r"(deed|document).{0,30}(registered|registration).{0,30}(land\s+registry|registrar)",
            "act": "Registration of Documents Ordinance",
            "section": "2",
            "rule": "Deeds affecting land must be registered.",
            "recommendation": "COMPLIANT: Registration requirement complies with Section 2."
        },
        {
            "pattern": r"(boundaries|extent|perches|acres|hectares|survey\s+plan|plan\s+number|lot\s+number)",
            "act": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "section": "2",
            "rule": "Property description including boundaries and extent must be specified.",
            "recommendation": "COMPLIANT: Property description properly specified."
        },
        {
            "pattern": r"(title|ownership|vendor).{0,30}(warrant|guarantee|free\s+from\s+encumbrance|good\s+and\s+marketable)",
            "act": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "section": "2",
            "rule": "Vendor must warrant good and marketable title.",
            "recommendation": "COMPLIANT: Title warranty properly included."
        },
        {
            "pattern": r"(consideration|purchase\s+price|sale\s+price).{0,30}(lkr|rupees|rs|amount|specified)",
            "act": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "section": "2",
            "rule": "Purchase price must be clearly stated.",
            "recommendation": "COMPLIANT: Purchase price properly stated."
        },
    ],

    # ========== ELECTRONIC CONTRACT / E-COMMERCE DOMAIN ==========
    "electronic_contract": [
        {
            "pattern": r"(electronic\s+contract|digital\s+contract|online\s+agreement).{0,30}(valid|enforceable|binding|lawful)",
            "act": "Electronic Transactions Act, No. 19 of 2006",
            "section": "4",
            "rule": "Electronic contracts are valid and enforceable.",
            "recommendation": "COMPLIANT: Electronic contract validity recognized under Section 4."
        },
        {
            "pattern": r"(electronic\s+signature|e-signature|digital\s+signature).{0,30}(valid|accepted|recognized|reliable)",
            "act": "Electronic Transactions Act, No. 19 of 2006",
            "section": "7",
            "rule": "Electronic signatures satisfy legal signature requirements.",
            "recommendation": "COMPLIANT: Electronic signature validity recognized under Section 7."
        },
        {
            "pattern": r"(electronic\s+record|digital\s+record|electronic\s+document).{0,30}(valid|maintained|retained|preserved)",
            "act": "Electronic Transactions Act, No. 19 of 2006",
            "section": "5",
            "rule": "Electronic records satisfy legal writing requirements.",
            "recommendation": "COMPLIANT: Electronic record validity recognized under Section 5."
        },
        {
            "pattern": r"(consent|agreement|acceptance).{0,30}(click|clicking|accept\s+button|check.?box|opt.?in)",
            "act": "Electronic Transactions Act, No. 19 of 2006",
            "section": "4",
            "rule": "Click-wrap and opt-in consent mechanisms are valid.",
            "recommendation": "COMPLIANT: Click-to-accept mechanism complies with Section 4."
        },
        {
            "pattern": r"(data\s+protection|privacy|personal\s+data).{0,30}(protect|secure|confidential|safeguard)",
            "act": "Electronic Transactions Act, No. 19 of 2006",
            "section": "General",
            "rule": "Data protection provisions are expected in e-commerce agreements.",
            "recommendation": "COMPLIANT: Data protection provision included."
        },
    ],
}


# General illegal patterns that apply to ALL contract types
GENERAL_ILLEGAL_PATTERNS = [
    {
        "pattern": r"(waive|waives|waiving|relinquish).{0,30}(all\s+rights?|statutory\s+rights?|legal\s+rights?)",
        "act": "Prevention of Frauds Ordinance",
        "section": "General",
        "rule": "Statutory rights granted by law cannot be waived by private contract.",
        "recommendation": "ILLEGAL: Statutory rights cannot be waived. Such clauses are void."
    },
    {
        "pattern": r"(no\s+right|shall\s+not\s+have\s+any\s+right|not\s+entitled).{0,30}(court|tribunal|legal\s+action|sue|lawsuit)",
        "act": "Constitution of Sri Lanka",
        "section": "Article 105",
        "rule": "Every person has the right of access to courts for the enforcement of rights.",
        "recommendation": "ILLEGAL: Access to courts is a constitutional right and cannot be contractually excluded."
    },
    {
        "pattern": r"(unilateral|sole\s+discretion|absolute\s+discretion).{0,30}(modify|change|amend|alter).{0,30}(terms|conditions|agreement)",
        "act": "Unfair Contract Terms Act",
        "section": "2",
        "rule": "Unilateral modification clauses may render a contract unconscionable.",
        "recommendation": "POTENTIALLY ILLEGAL: Unilateral right to modify terms without consent may be void."
    },
    {
        "pattern": r"(entire\s+liability|maximum\s+liability|total\s+liability).{0,30}(shall\s+not\s+exceed|limited\s+to).{0,20}(zero|nil|nothing|0)",
        "act": "Unfair Contract Terms Act",
        "section": "2",
        "rule": "Exclusion clauses for negligence causing death or injury are void; other exclusions must be reasonable.",
        "recommendation": "ILLEGAL: Complete exclusion of all liability is likely void under Section 2."
    },
    {
        "pattern": r"(arbitration|dispute).{0,30}(foreign\s+jurisdiction|overseas|abroad|outside\s+sri\s+lanka).{0,30}(exclusive)",
        "act": "Arbitration Act",
        "section": "General",
        "rule": "Choice of foreign jurisdiction clauses should be carefully reviewed.",
        "recommendation": "REVIEW: Exclusive foreign jurisdiction clauses may limit access to local remedies."
    },
    {
        "pattern": r"(binding|bound).{0,30}(third\s+parties?|successors|assigns).{0,30}(without\s+consent|automatically)",
        "act": "Prevention of Frauds Ordinance",
        "section": "2",
        "rule": "Contracts cannot generally bind third parties without their consent.",
        "recommendation": "REVIEW: Clauses purporting to bind third parties may not be enforceable."
    },
]


def split_into_clauses(text):
    """Split text into meaningful clauses"""
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])|(?:\n\s*\n+)', text)
    clauses = []
    for s in sentences:
        s = s.strip()
        if len(s) > 40:
            clauses.append(s)
    return clauses


def check_pattern_match(clause, patterns):
    """Check if clause matches any pattern"""
    clause_clean = re.sub(r'\s+', ' ', clause.lower())
    for pattern_info in patterns:
        if re.search(pattern_info["pattern"], clause_clean, re.IGNORECASE | re.DOTALL):
            return pattern_info
    return None


def get_category_law_info(category, domain):
    """Get law reference info based on clause category"""
    if category in CATEGORY_LAW_MAPPING:
        return CATEGORY_LAW_MAPPING[category]
    
    # Default based on domain - using correct Sri Lankan laws
    domain_defaults = {
        "employment": {
            "act": "Shop and Office Employees Act",
            "section": "General",
            "rule": "Standard employment contract clause governed by employment laws."
        },
        "rental": {
            "act": "Rent Act",
            "section": "General",
            "rule": "Standard rental agreement clause governed by the Rent Act."
        },
        "finance_leasing": {
            "act": "Finance Leasing Act, No. 56 of 2000",
            "section": "General",
            "rule": "Standard finance leasing clause governed by the Finance Leasing Act."
        },
        "consumer": {
            "act": "Consumer Affairs Authority Act",
            "section": "General",
            "rule": "Standard consumer contract clause governed by consumer protection laws."
        },
        "partnership": {
            "act": "Partnership Ordinance",
            "section": "General",
            "rule": "Standard partnership agreement clause governed by the Partnership Ordinance."
        },
        "sale_of_goods": {
            "act": "Sale of Goods Ordinance, No. 11 of 1896",
            "section": "General",
            "rule": "Standard sale of goods clause governed by the Sale of Goods Ordinance."
        },
        "microfinance": {
            "act": "Microfinance Act No. 6 of 2016",
            "section": "General",
            "rule": "Standard microfinance/lending clause governed by the Microfinance Act and Money Lending Ordinance."
        },
        "pawn_pledge": {
            "act": "Pawnbrokers Ordinance",
            "section": "General",
            "rule": "Standard pawn/pledge clause governed by the Pawnbrokers Ordinance."
        },
        "land_property": {
            "act": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "section": "2",
            "rule": "Standard land/property sale clause governed by the Prevention of Frauds Ordinance."
        },
        "electronic_contract": {
            "act": "Electronic Transactions Act, No. 19 of 2006",
            "section": "4",
            "rule": "Standard electronic contract clause governed by the Electronic Transactions Act."
        },
        "general": {
            "act": "Prevention of Frauds Ordinance",
            "section": "2",
            "rule": "Standard contract clause governed by general contract law principles."
        }
    }
    return domain_defaults.get(domain, domain_defaults["general"])


# ==============================
# MANDATORY CLAUSES DEFINITION (By Domain)
# Based on Sri Lankan Legal Acts
# ==============================

MANDATORY_CLAUSES = {
    "employment": [
        {
            "id": "salary",
            "name": "Salary/Compensation",
            "description": "Monthly salary, payment schedule, and method",
            "legal_basis": "Shop and Office Employees Act, Wages Boards Ordinance",
            "keywords": ["salary", "wage", "wages", "remuneration", "compensation", "pay", "payment", "lkr", "rs.", "monthly pay", "basic salary", "gross salary"],
            "patterns": [r"salary\s*(of|is|shall\s+be)?\s*[\d,]+", r"monthly\s+(salary|pay|wage)", r"remuneration", r"compensation\s+(of|shall)"],
            "nli_premise": "Employment contracts must specify the employee's salary or compensation amount and payment terms."
        },
        {
            "id": "working_hours",
            "name": "Working Hours",
            "description": "Daily and weekly working hours as per Shop and Office Act",
            "legal_basis": "Shop and Office Employees Act",
            "keywords": ["working hours", "work hours", "hours of work", "working time", "8 hours", "9 to 5", "9am", "5pm", "duty hours", "office hours", "shift"],
            "patterns": [r"working\s+hours", r"hours\s+of\s+work", r"\d+\s*hours?\s*(per|a)\s*(day|week)", r"(monday|mon)\s*to\s*(friday|fri|saturday|sat)"],
            "nli_premise": "Employment contracts must specify the daily and weekly working hours of the employee."
        },
        {
            "id": "epf",
            "name": "EPF Contributions",
            "description": "Employees' Provident Fund contributions (8% employee, 12% employer)",
            "legal_basis": "Employees' Provident Fund Act",
            "keywords": ["epf", "provident fund", "employees' provident", "employee provident", "8%", "12%", "epf contribution"],
            "patterns": [r"epf", r"provident\s+fund", r"(8|12)\s*%\s*(employee|employer)?"],
            "nli_premise": "Employment contracts must include EPF (Employees' Provident Fund) contribution terms with 8% employee and 12% employer contributions."
        },
        {
            "id": "etf",
            "name": "ETF Contributions",
            "description": "Employees' Trust Fund contributions (3% employer)",
            "legal_basis": "Employees' Trust Fund Act",
            "keywords": ["etf", "trust fund", "employees' trust", "employee trust", "3%", "etf contribution"],
            "patterns": [r"etf", r"trust\s+fund", r"3\s*%\s*(employer)?"],
            "nli_premise": "Employment contracts must include ETF (Employees' Trust Fund) contribution terms with 3% employer contribution."
        },
        {
            "id": "leave_policy",
            "name": "Leave Policy",
            "description": "Annual leave, sick leave, and casual leave entitlements",
            "legal_basis": "Shop and Office Employees Act",
            "keywords": ["leave", "annual leave", "sick leave", "casual leave", "vacation", "holiday", "leave entitlement", "paid leave", "days off", "leave days"],
            "patterns": [r"(annual|sick|casual|paid)\s+leave", r"leave\s+(entitlement|policy|days)", r"\d+\s+days?\s+(of\s+)?leave"],
            "nli_premise": "Employment contracts must specify leave entitlements including annual leave, sick leave, and casual leave."
        },
        {
            "id": "termination",
            "name": "Termination Clause",
            "description": "Notice period, termination conditions, and severance",
            "legal_basis": "Termination of Employment of Workmen Act",
            "keywords": ["termination", "terminate", "dismissal", "discharge", "end of employment", "cessation", "separation"],
            "patterns": [r"terminat(ion|e|ed|ing)", r"dismiss(al|ed)?", r"end\s+of\s+employment", r"separation\s+from\s+service"],
            "nli_premise": "Employment contracts must include termination conditions and procedures as per Termination of Employment of Workmen Act."
        },
        {
            "id": "probation",
            "name": "Probation Period",
            "description": "Duration and conditions of probationary period",
            "legal_basis": "Industrial Disputes Act",
            "keywords": ["probation", "probationary", "trial period", "provisional", "confirmation", "probation period"],
            "patterns": [r"probation(ary)?(\s+period)?", r"trial\s+period", r"\d+\s+months?\s+probation"],
            "nli_premise": "Employment contracts should specify any probationary period and conditions for confirmation."
        },
        {
            "id": "job_description",
            "name": "Job Description",
            "description": "Duties and responsibilities of the employee",
            "legal_basis": "Industrial Disputes Act, Shop and Office Employees Act",
            "keywords": ["duties", "responsibilities", "job description", "role", "position", "designation", "job title", "scope of work", "tasks"],
            "patterns": [r"(duties|responsibilities)\s+(of|include|are)", r"job\s+(description|title|role)", r"position\s+of", r"designation"],
            "nli_premise": "Employment contracts must clearly define the employee's job title, duties, and responsibilities."
        },
        {
            "id": "maternity",
            "name": "Maternity Benefits",
            "description": "Maternity leave as per Maternity Benefits Ordinance",
            "legal_basis": "Maternity Benefits Ordinance",
            "keywords": ["maternity", "maternity leave", "pregnancy", "childbirth", "prenatal", "postnatal", "maternity benefits"],
            "patterns": [r"maternity\s+(leave|benefit)", r"pregnan(cy|t)", r"(pre|post)natal"],
            "nli_premise": "Employment contracts must include maternity leave and benefits as per the Maternity Benefits Ordinance."
        },
        {
            "id": "overtime",
            "name": "Overtime Provisions",
            "description": "Overtime rates and conditions",
            "legal_basis": "Wages Boards Ordinance",
            "keywords": ["overtime", "extra hours", "additional hours", "ot", "overtime pay", "overtime rate", "time and half", "double time"],
            "patterns": [r"overtime", r"extra\s+hours", r"(1\.5|1\.25|2)\s*x?\s*(pay|rate)?", r"time\s+and\s+(a\s+)?half"],
            "nli_premise": "Employment contracts must specify overtime work conditions and compensation rates."
        },
        {
            "id": "gratuity",
            "name": "Gratuity Entitlement",
            "description": "Gratuity payment upon completion of service",
            "legal_basis": "Payment of Gratuity Act",
            "keywords": ["gratuity", "service gratuity", "terminal benefits", "end of service", "gratuity payment"],
            "patterns": [r"gratuity", r"terminal\s+benefit", r"end\s+of\s+service\s+(payment|benefit)"],
            "nli_premise": "Employment contracts should reference gratuity entitlements as per the Payment of Gratuity Act."
        },
        {
            "id": "notice_period",
            "name": "Notice Period & Severance",
            "description": "Required notice period for termination and severance pay",
            "legal_basis": "Termination of Employment of Workmen Act",
            "keywords": ["notice period", "notice", "severance", "resignation notice", "termination notice", "one month notice", "two weeks notice"],
            "patterns": [r"notice\s+period", r"(one|two|three|1|2|3)\s+(month|week)s?\s+notice", r"severance\s+(pay|payment)?"],
            "nli_premise": "Employment contracts must specify the notice period required for termination or resignation."
        },
        {
            "id": "minimum_wage",
            "name": "Minimum Wages",
            "description": "Compliance with minimum wage requirements",
            "legal_basis": "Wages Boards Ordinance",
            "keywords": ["minimum wage", "minimum pay", "basic wage", "statutory minimum", "wages board"],
            "patterns": [r"minimum\s+wage", r"wages?\s+board", r"statutory\s+minimum"],
            "nli_premise": "Employment contracts must comply with minimum wage requirements under the Wages Boards Ordinance."
        },
        {
            "id": "employee_identification",
            "name": "Employee Name & Job Title",
            "description": "Clear identification of employee and position",
            "legal_basis": "Industrial Disputes Act, Shop and Office Employees Act",
            "keywords": ["employee name", "name of employee", "hereinafter", "employee", "appointed as", "engaged as", "position of"],
            "patterns": [r"(employee|staff)\s+name", r"appointed\s+(as|to)", r"engaged\s+as", r"mr\.|mrs\.|ms\.|dr\."],
            "nli_premise": "Employment contracts must clearly identify the employee by name and specify their job title or position."
        }
    ],
    
    "consumer": [
        {
            "id": "loan_amount",
            "name": "Loan/Principal Amount",
            "description": "The principal loan amount clearly stated",
            "legal_basis": "Money Lending Ordinance, Consumer Credit Act",
            "keywords": ["loan amount", "principal", "principal amount", "loan", "credit amount", "lkr", "rs.", "borrowed amount", "facility amount"],
            "patterns": [r"(loan|principal|credit)\s+(amount|sum)", r"(lkr|rs\.?)\s*[\d,]+", r"amount\s+of\s+(loan|credit)"],
            "nli_premise": "Loan agreements must clearly specify the principal loan amount."
        },
        {
            "id": "interest_rate",
            "name": "Interest Rate & Calculation Method",
            "description": "Interest rate and how it is calculated",
            "legal_basis": "Consumer Credit Act, Money Lending Ordinance",
            "keywords": ["interest", "interest rate", "rate of interest", "annual rate", "per annum", "p.a.", "apr", "monthly interest", "flat rate", "reducing balance"],
            "patterns": [r"interest\s+rate", r"\d+(\.\d+)?\s*%\s*(per\s+annum|p\.?a\.?)?", r"(flat|reducing)\s+(rate|balance)"],
            "nli_premise": "Loan agreements must specify the interest rate and calculation method clearly."
        },
        {
            "id": "repayment_schedule",
            "name": "Repayment Schedule",
            "description": "Installments, due dates, and repayment terms",
            "legal_basis": "Consumer Credit Act",
            "keywords": ["repayment", "installment", "emi", "monthly payment", "due date", "payment schedule", "repayment schedule", "amortization"],
            "patterns": [r"repayment\s+(schedule|term)", r"(monthly|weekly)\s+installment", r"emi", r"due\s+(date|on)"],
            "nli_premise": "Loan agreements must include a clear repayment schedule with installment amounts and due dates."
        },
        {
            "id": "borrower_rights",
            "name": "Borrower Rights",
            "description": "Early settlement rights, complaint procedures",
            "legal_basis": "Consumer Credit Act, Consumer Affairs Authority Act",
            "keywords": ["borrower rights", "early settlement", "prepayment", "complaint", "grievance", "consumer rights", "right to repay", "right to settle"],
            "patterns": [r"(borrower|consumer)\s+rights?", r"early\s+(settlement|repayment)", r"prepay(ment)?", r"complaint\s+(procedure|mechanism)"],
            "nli_premise": "Loan agreements must inform borrowers of their rights including early settlement and complaint procedures."
        },
        {
            "id": "late_payment_penalty",
            "name": "Penalty for Late Payment",
            "description": "Reasonable and legally permitted late fees",
            "legal_basis": "Unfair Contract Terms Act",
            "keywords": ["late payment", "penalty", "late fee", "default interest", "overdue", "arrears", "late charge"],
            "patterns": [r"late\s+(payment|fee|charge|penalty)", r"default\s+interest", r"overdue\s+(payment|charge)", r"arrears"],
            "nli_premise": "Loan agreements must specify reasonable late payment penalties that comply with the Unfair Contract Terms Act."
        },
        {
            "id": "debt_recovery",
            "name": "Debt Recovery Procedures",
            "description": "Collection and recovery procedures",
            "legal_basis": "Money Lending Ordinance, Prevention of Frauds Ordinance",
            "keywords": ["debt recovery", "collection", "recovery", "enforcement", "legal action", "default", "recovery procedure"],
            "patterns": [r"debt\s+recovery", r"(collection|recovery)\s+procedure", r"legal\s+action", r"enforcement"],
            "nli_premise": "Loan agreements must outline debt recovery and collection procedures."
        },
        {
            "id": "assignment_of_debt",
            "name": "Assignment of Debt",
            "description": "Terms for transferring the debt to third parties",
            "legal_basis": "Prevention of Frauds Ordinance",
            "keywords": ["assignment", "transfer", "assign", "third party", "successor", "assignee"],
            "patterns": [r"assign(ment|ed)?", r"transfer\s+(of\s+)?(debt|loan|rights)", r"third\s+party"],
            "nli_premise": "Loan agreements must specify conditions for assignment or transfer of debt to third parties."
        },
        {
            "id": "written_modifications",
            "name": "Written Modifications Only",
            "description": "Agreement can only be modified in writing",
            "legal_basis": "Registration of Documents Ordinance",
            "keywords": ["written modification", "amendment", "variation", "in writing", "written consent", "written agreement"],
            "patterns": [r"(modification|amendment|variation)s?\s+(in\s+)?writing", r"written\s+(consent|agreement|modification)"],
            "nli_premise": "Loan agreements must require that any modifications be made in writing."
        },
        {
            "id": "electronic_validity",
            "name": "Electronic Communications",
            "description": "Validity of electronic signatures and communications",
            "legal_basis": "Electronic Transactions Act",
            "keywords": ["electronic", "email", "digital", "electronic signature", "e-signature", "electronic communication"],
            "patterns": [r"electronic\s+(signature|communication|mail|transaction)", r"e-?mail", r"digital\s+signature"],
            "nli_premise": "Loan agreements may specify the validity of electronic communications and signatures under the Electronic Transactions Act."
        },
        {
            "id": "limitation_of_liability",
            "name": "Limitation of Liability",
            "description": "Cannot waive statutory obligations",
            "legal_basis": "Unfair Contract Terms Act",
            "keywords": ["liability", "limitation", "limit liability", "exclusion", "indemnity", "waiver"],
            "patterns": [r"limit(ation)?\s+(of\s+)?liability", r"exclu(de|sion)", r"indemnif(y|ication)"],
            "nli_premise": "Loan agreements must not unfairly limit liability or waive statutory consumer protections."
        },
        {
            "id": "signatures",
            "name": "Signatures of Parties",
            "description": "Both parties must sign the agreement",
            "legal_basis": "Money Lending Ordinance",
            "keywords": ["signature", "signed", "sign", "witness", "executed", "parties signed"],
            "patterns": [r"sign(ed|ature)?", r"witness(ed)?", r"execut(ed|ion)", r"parties\s+(have\s+)?signed"],
            "nli_premise": "Loan agreements must be signed by all parties to be legally valid."
        },
        {
            "id": "sale_delivery_terms",
            "name": "Sale/Delivery of Goods Terms",
            "description": "Terms for sale and delivery of goods",
            "legal_basis": "Sale of Goods Ordinance",
            "keywords": ["sale", "delivery", "goods", "merchandise", "product", "transfer of title", "delivery terms"],
            "patterns": [r"(sale|delivery)\s+of\s+goods", r"transfer\s+of\s+title", r"delivery\s+(terms|date|method)"],
            "nli_premise": "Consumer agreements involving goods must specify sale and delivery terms."
        }
    ],
    
    "rental": [
        {
            "id": "parties",
            "name": "Parties' Names & Addresses",
            "description": "Full names and addresses of landlord and tenant",
            "legal_basis": "Rent Act",
            "keywords": ["landlord", "tenant", "lessor", "lessee", "owner", "occupier", "address", "residing at", "party"],
            "patterns": [r"(landlord|tenant|lessor|lessee)", r"residing\s+at", r"(first|second)\s+party"],
            "nli_premise": "Rental agreements must clearly identify the landlord and tenant with their names and addresses."
        },
        {
            "id": "property_description",
            "name": "Description of Property",
            "description": "Clear description of the rental property",
            "legal_basis": "Rent Act",
            "keywords": ["property", "premises", "located at", "situated at", "address", "building", "apartment", "flat", "house", "unit"],
            "patterns": [r"(property|premises)\s+(located|situated|at)", r"(apartment|flat|house|unit)\s+(no\.?|number)?"],
            "nli_premise": "Rental agreements must contain a clear description of the rental property."
        },
        {
            "id": "rent_amount",
            "name": "Rent Amount & Payment Method",
            "description": "Monthly rent and how/when to pay",
            "legal_basis": "Rent Act",
            "keywords": ["rent", "monthly rent", "rental", "lkr", "rs.", "payment", "rent amount", "payable"],
            "patterns": [r"(monthly\s+)?rent\s*(of|is|amount)?", r"(lkr|rs\.?)\s*[\d,]+", r"rent\s+payable"],
            "nli_premise": "Rental agreements must specify the rent amount and payment method."
        },
        {
            "id": "duration",
            "name": "Duration of Tenancy",
            "description": "Start and end date of the rental period",
            "legal_basis": "Rent Act",
            "keywords": ["term", "duration", "period", "commence", "start date", "end date", "tenancy period", "lease term", "year", "month"],
            "patterns": [r"(term|duration|period)\s+(of|is)", r"commenc(e|ing)", r"(start|end)\s+date", r"\d+\s+(year|month)s?"],
            "nli_premise": "Rental agreements must specify the duration of the tenancy."
        },
        {
            "id": "security_deposit",
            "name": "Security Deposit",
            "description": "Deposit amount and refund conditions",
            "legal_basis": "Rent Act",
            "keywords": ["security deposit", "deposit", "advance", "refundable", "security", "caution deposit"],
            "patterns": [r"security\s+deposit", r"(advance|deposit)\s+(of|amount)", r"refund(able)?"],
            "nli_premise": "Rental agreements must specify any security deposit amount and refund conditions."
        },
        {
            "id": "termination_notice",
            "name": "Termination/Notice Period",
            "description": "Notice required to end tenancy",
            "legal_basis": "Rent Act",
            "keywords": ["termination", "notice", "notice period", "vacate", "end tenancy", "terminate tenancy"],
            "patterns": [r"(termination|notice)\s+period", r"(one|two|three|1|2|3)\s+months?\s+notice", r"vacate"],
            "nli_premise": "Rental agreements must specify the notice period required for termination."
        },
        {
            "id": "rights_obligations",
            "name": "Rights & Obligations",
            "description": "Rights and duties of tenant and landlord",
            "legal_basis": "Rent Act",
            "keywords": ["rights", "obligations", "duties", "responsibilities", "tenant shall", "landlord shall", "maintain", "repairs"],
            "patterns": [r"(rights|obligations|duties)", r"(tenant|landlord)\s+shall", r"(maintain|repair)"],
            "nli_premise": "Rental agreements must outline the rights and obligations of both landlord and tenant."
        },
        {
            "id": "registration",
            "name": "Registration of Agreement",
            "description": "Registration of rental agreement if applicable",
            "legal_basis": "Registration of Documents Ordinance",
            "keywords": ["registration", "registered", "register", "registrar", "stamp duty", "notarized", "notary"],
            "patterns": [r"regist(er|ration|ered)", r"notari(ze|zed)", r"stamp\s+duty"],
            "nli_premise": "Rental agreements may need to be registered under the Registration of Documents Ordinance for certain tenancy types."
        }
    ],
    
    "finance_leasing": [
        {
            "id": "lease_rental",
            "name": "Lease Rental Amount",
            "description": "Monthly lease rental payment amount",
            "legal_basis": "Finance Leasing Act",
            "keywords": ["lease rental", "monthly rental", "rental amount", "lkr", "rs.", "installment", "lease payment"],
            "patterns": [r"lease\s+rental", r"monthly\s+(rental|payment)", r"(lkr|rs\.?)\s*[\d,]+"],
            "nli_premise": "Finance leasing agreements must specify the lease rental amount."
        },
        {
            "id": "lease_term",
            "name": "Lease Term/Period",
            "description": "Duration of the lease",
            "legal_basis": "Finance Leasing Act",
            "keywords": ["lease term", "period", "duration", "months", "years", "tenure", "lease period"],
            "patterns": [r"lease\s+(term|period)", r"\d+\s+(month|year)s?", r"tenure"],
            "nli_premise": "Finance leasing agreements must specify the lease term or period."
        },
        {
            "id": "asset_description",
            "name": "Equipment/Vehicle Description",
            "description": "Detailed description of the leased asset",
            "legal_basis": "Finance Leasing Act",
            "keywords": ["vehicle", "equipment", "asset", "motor", "machinery", "registration", "chassis", "engine", "make", "model"],
            "patterns": [r"(vehicle|equipment|asset|machinery)", r"(registration|chassis|engine)\s+(no\.?|number)", r"(make|model|year)"],
            "nli_premise": "Finance leasing agreements must clearly describe the leased vehicle or equipment."
        },
        {
            "id": "insurance",
            "name": "Insurance Requirements",
            "description": "Insurance obligations for the leased asset",
            "legal_basis": "Finance Leasing Act",
            "keywords": ["insurance", "comprehensive", "insure", "policy", "coverage", "insured"],
            "patterns": [r"insurance", r"comprehensive\s+(insurance|coverage)", r"insur(e|ed|ance)"],
            "nli_premise": "Finance leasing agreements must specify insurance requirements for the leased asset."
        },
        {
            "id": "repossession",
            "name": "Repossession Rights",
            "description": "Conditions under which asset can be repossessed",
            "legal_basis": "Finance Leasing Act",
            "keywords": ["repossession", "repossess", "seize", "recovery", "default", "take back"],
            "patterns": [r"reposses(s|sion)", r"seiz(e|ure)", r"recover(y)?"],
            "nli_premise": "Finance leasing agreements must outline repossession rights and procedures."
        },
        {
            "id": "ownership_transfer",
            "name": "Ownership Transfer",
            "description": "Terms for transfer of ownership at end of lease",
            "legal_basis": "Finance Leasing Act",
            "keywords": ["ownership", "transfer", "title", "purchase option", "buyout", "own"],
            "patterns": [r"(ownership|title)\s+transfer", r"purchase\s+option", r"buy(-)?out"],
            "nli_premise": "Finance leasing agreements should specify ownership transfer conditions at end of lease."
        }
    ],
    
    "partnership": [
        {
            "id": "partners",
            "name": "Partners' Names & Capital",
            "description": "Names of all partners and their capital contributions",
            "legal_basis": "Partnership Ordinance",
            "keywords": ["partner", "partners", "capital", "contribution", "investment", "share capital"],
            "patterns": [r"partner(s)?", r"capital\s+(contribution|investment)", r"(first|second|third)\s+partner"],
            "nli_premise": "Partnership agreements must identify all partners and their capital contributions."
        },
        {
            "id": "profit_sharing",
            "name": "Profit/Loss Sharing Ratio",
            "description": "How profits and losses are divided",
            "legal_basis": "Partnership Ordinance",
            "keywords": ["profit", "loss", "sharing", "ratio", "distribution", "divide", "share"],
            "patterns": [r"profit\s+(sharing|distribution|ratio)", r"loss\s+sharing", r"\d+:\d+\s+ratio"],
            "nli_premise": "Partnership agreements must specify the profit and loss sharing ratio among partners."
        },
        {
            "id": "duties",
            "name": "Duties & Responsibilities",
            "description": "Roles and responsibilities of each partner",
            "legal_basis": "Partnership Ordinance",
            "keywords": ["duties", "responsibilities", "role", "manage", "management", "authority", "partner duties"],
            "patterns": [r"(duties|responsibilities)\s+of", r"manage(ment)?", r"(role|authority)\s+of"],
            "nli_premise": "Partnership agreements must define the duties and responsibilities of each partner."
        },
        {
            "id": "decision_making",
            "name": "Decision-Making Authority",
            "description": "How decisions are made in the partnership",
            "legal_basis": "Partnership Ordinance",
            "keywords": ["decision", "vote", "voting", "authority", "consent", "approval", "unanimous", "majority"],
            "patterns": [r"decision(-|\s)?making", r"vot(e|ing)", r"(unanimous|majority)\s+(consent|approval)"],
            "nli_premise": "Partnership agreements must outline decision-making authority and procedures."
        },
        {
            "id": "partnership_duration",
            "name": "Duration of Partnership",
            "description": "How long the partnership will last",
            "legal_basis": "Partnership Ordinance",
            "keywords": ["duration", "term", "period", "commence", "indefinite", "fixed term"],
            "patterns": [r"(duration|term)\s+of\s+partnership", r"(fixed|indefinite)\s+term"],
            "nli_premise": "Partnership agreements must specify the duration of the partnership."
        },
        {
            "id": "dissolution",
            "name": "Termination/Dissolution Terms",
            "description": "How the partnership can be ended",
            "legal_basis": "Partnership Ordinance",
            "keywords": ["dissolution", "terminate", "termination", "wind up", "winding up", "dissolve", "end partnership"],
            "patterns": [r"dissol(ve|ution)", r"terminat(e|ion)", r"wind(ing)?\s+up"],
            "nli_premise": "Partnership agreements must include dissolution and termination procedures."
        },
        {
            "id": "partner_signatures",
            "name": "Signatures of All Partners",
            "description": "All partners must sign the agreement",
            "legal_basis": "Partnership Ordinance",
            "keywords": ["signature", "signed", "sign", "witness", "executed"],
            "patterns": [r"sign(ed|ature)?", r"witness(ed)?", r"execut(ed|ion)"],
            "nli_premise": "Partnership agreements must be signed by all partners."
        }
    ],

    # ========== SALE OF GOODS DOMAIN ==========
    "sale_of_goods": [
        {
            "id": "goods_description",
            "name": "Description of Goods",
            "description": "Clear description of goods being sold",
            "legal_basis": "Sale of Goods Ordinance, No. 11 of 1896",
            "keywords": ["goods", "product", "description", "specifications", "merchandise", "item", "quantity"],
            "patterns": [r"(goods|product|merchandise)\s+(descri|specif)", r"quantity"],
            "nli_premise": "Sale of goods agreements must clearly describe the goods being sold."
        },
        {
            "id": "sale_price",
            "name": "Price/Consideration",
            "description": "Purchase price must be specified",
            "legal_basis": "Sale of Goods Ordinance, No. 11 of 1896",
            "keywords": ["price", "consideration", "purchase price", "amount", "payment", "cost"],
            "patterns": [r"(price|consideration|amount|cost)", r"(lkr|rupees|rs)"],
            "nli_premise": "Sale of goods agreements must specify the purchase price."
        },
        {
            "id": "delivery_terms",
            "name": "Delivery Terms",
            "description": "When and how goods will be delivered",
            "legal_basis": "Sale of Goods Ordinance, No. 11 of 1896",
            "keywords": ["delivery", "deliver", "shipment", "dispatch", "collection", "transit"],
            "patterns": [r"deliver(y|ed)?", r"(ship|dispatch|transit)"],
            "nli_premise": "Sale of goods agreements must specify delivery terms."
        },
        {
            "id": "quality_warranty",
            "name": "Quality/Warranty Terms",
            "description": "Merchantable quality and warranty provisions",
            "legal_basis": "Sale of Goods Ordinance, No. 11 of 1896",
            "keywords": ["warranty", "guarantee", "quality", "merchantable", "defect", "fitness"],
            "patterns": [r"warrant(y|ies)?", r"guarantee", r"(merchantable|quality|defect)"],
            "nli_premise": "Sale of goods agreements should include quality warranties."
        },
        {
            "id": "payment_terms",
            "name": "Payment Terms",
            "description": "How and when payment will be made",
            "legal_basis": "Sale of Goods Ordinance, No. 11 of 1896",
            "keywords": ["payment", "pay", "installment", "advance", "cash", "credit", "bank transfer"],
            "patterns": [r"payment", r"(installment|advance|credit)"],
            "nli_premise": "Sale of goods agreements must specify payment terms."
        }
    ],

    # ========== MICROFINANCE / LENDING DOMAIN ==========
    "microfinance": [
        {
            "id": "loan_amount",
            "name": "Principal/Loan Amount",
            "description": "Principal amount must be clearly stated",
            "legal_basis": "Money Lending Ordinance, No. 2 of 1918",
            "keywords": ["principal", "loan amount", "sum", "borrowed", "advanced"],
            "patterns": [r"(principal|loan\s+amount|sum)", r"(lkr|rupees|rs)"],
            "nli_premise": "Loan agreements must clearly state the principal amount."
        },
        {
            "id": "interest_rate",
            "name": "Interest Rate Disclosure",
            "description": "Interest rate must be clearly stated",
            "legal_basis": "Money Lending Ordinance, No. 2 of 1918",
            "keywords": ["interest", "rate", "per annum", "annual", "percentage", "flat rate"],
            "patterns": [r"interest\s+rate", r"per\s+annum", r"\d+\s*%"],
            "nli_premise": "Loan agreements must clearly disclose the interest rate."
        },
        {
            "id": "repayment_schedule",
            "name": "Repayment Schedule",
            "description": "Repayment terms and schedule",
            "legal_basis": "Money Lending Ordinance, No. 2 of 1918",
            "keywords": ["repayment", "installment", "monthly", "schedule", "due date", "payment plan"],
            "patterns": [r"repay(ment)?", r"installment", r"(monthly|weekly)\s+payment"],
            "nli_premise": "Loan agreements must specify the repayment schedule."
        },
        {
            "id": "total_cost",
            "name": "Total Cost of Borrowing",
            "description": "Total amount payable including fees and charges",
            "legal_basis": "Money Lending Ordinance, No. 2 of 1918",
            "keywords": ["total cost", "total amount", "total payable", "fees", "charges", "processing fee"],
            "patterns": [r"total\s+(cost|amount|payable)", r"(fees|charges)"],
            "nli_premise": "Loan agreements must disclose the total cost of borrowing."
        },
        {
            "id": "written_agreement",
            "name": "Written Agreement",
            "description": "Agreement must be in writing",
            "legal_basis": "Money Lending Ordinance, No. 2 of 1918",
            "keywords": ["written", "in writing", "signed", "executed", "agreement"],
            "patterns": [r"(in\s+writing|written\s+agreement)", r"sign(ed|ature)?"],
            "nli_premise": "Loan agreements must be in writing as required by law."
        },
        {
            "id": "default_terms",
            "name": "Default/Late Payment Terms",
            "description": "Consequences of default or late payment",
            "legal_basis": "Money Lending Ordinance, No. 2 of 1918",
            "keywords": ["default", "late payment", "overdue", "arrears", "penalty"],
            "patterns": [r"default", r"late\s+payment", r"(overdue|arrears|penalty)"],
            "nli_premise": "Loan agreements must specify default and late payment consequences."
        }
    ],

    # ========== PAWN / PLEDGE DOMAIN ==========
    "pawn_pledge": [
        {
            "id": "pledged_item_description",
            "name": "Description of Pledged Item",
            "description": "Pledged item must be clearly described",
            "legal_basis": "Pawnbrokers Ordinance",
            "keywords": ["pledged item", "article", "gold", "jewelry", "jewellery", "description", "item"],
            "patterns": [r"(pledged|pawn)\s+(item|article)", r"(gold|jewel)"],
            "nli_premise": "Pawn agreements must clearly describe the pledged item."
        },
        {
            "id": "loan_amount_pawn",
            "name": "Loan Amount Against Pledge",
            "description": "Amount advanced against the pledge",
            "legal_basis": "Pawnbrokers Ordinance",
            "keywords": ["loan amount", "advanced", "sum", "amount", "principal"],
            "patterns": [r"(loan|amount|sum)\s+(advanced|lent)", r"(lkr|rupees|rs)"],
            "nli_premise": "Pawn agreements must state the loan amount advanced."
        },
        {
            "id": "redemption_period",
            "name": "Redemption Period",
            "description": "Time allowed to redeem the pledge",
            "legal_basis": "Pawnbrokers Ordinance",
            "keywords": ["redemption", "redeem", "period", "months", "days", "expiry", "deadline"],
            "patterns": [r"redemption\s+period", r"redeem\s+within", r"\d+\s+(months?|days?)"],
            "nli_premise": "Pawn agreements must specify the redemption period."
        },
        {
            "id": "pawn_ticket",
            "name": "Pawn Ticket/Receipt",
            "description": "Receipt must be issued for every pledge",
            "legal_basis": "Pawnbrokers Ordinance",
            "keywords": ["pawn ticket", "receipt", "acknowledgment", "token"],
            "patterns": [r"pawn\s+ticket", r"receipt", r"acknowledg"],
            "nli_premise": "A pawn ticket or receipt must be issued for every pledge."
        },
        {
            "id": "interest_charges_pawn",
            "name": "Interest/Charges",
            "description": "Interest and charges must be specified",
            "legal_basis": "Pawnbrokers Ordinance",
            "keywords": ["interest", "charges", "rate", "fee", "cost"],
            "patterns": [r"interest", r"charges?", r"(rate|fee)"],
            "nli_premise": "Pawn agreements must specify interest rates and charges."
        }
    ],

    # ========== PROPERTY / LAND SALE DOMAIN ==========
    "land_property": [
        {
            "id": "property_description",
            "name": "Property Description",
            "description": "Full description including boundaries, extent, and plan number",
            "legal_basis": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "keywords": ["boundaries", "extent", "perches", "acres", "survey plan", "plan number", "lot", "land"],
            "patterns": [r"(boundaries|extent|perches|acres)", r"(plan|survey)\s+n", r"(lot|land)"],
            "nli_premise": "Land sale deeds must contain a full description of the property including boundaries and extent."
        },
        {
            "id": "notarial_attestation",
            "name": "Notarial Attestation",
            "description": "Deed must be attested by a notary public",
            "legal_basis": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "keywords": ["notary", "notarial", "attested", "attestation", "notary public"],
            "patterns": [r"notar(y|ial)", r"attest(ed|ation)?"],
            "nli_premise": "Land sale deeds must be attested by a notary public."
        },
        {
            "id": "witnesses",
            "name": "Two Witnesses",
            "description": "Deed must be signed before two witnesses",
            "legal_basis": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "keywords": ["witness", "witnesses", "two witnesses", "attesting witness"],
            "patterns": [r"witness(es)?", r"two\s+witness"],
            "nli_premise": "Land sale deeds must be signed before two witnesses."
        },
        {
            "id": "purchase_price_land",
            "name": "Purchase Price/Consideration",
            "description": "Sale price must be specified",
            "legal_basis": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "keywords": ["price", "consideration", "purchase price", "sale price", "amount"],
            "patterns": [r"(price|consideration)", r"(lkr|rupees|rs)"],
            "nli_premise": "Land sale deeds must clearly state the purchase price."
        },
        {
            "id": "title_warranty",
            "name": "Title Warranty",
            "description": "Vendor must warrant good title",
            "legal_basis": "Prevention of Frauds Ordinance, No. 7 of 1840",
            "keywords": ["title", "ownership", "free from encumbrance", "good title", "marketable title"],
            "patterns": [r"(title|ownership)", r"(encumbrance|marketable)"],
            "nli_premise": "Land sale deeds must include a warranty of good and marketable title."
        },
        {
            "id": "registration",
            "name": "Registration of Deed",
            "description": "Deed must be registered in the Land Registry",
            "legal_basis": "Registration of Documents Ordinance",
            "keywords": ["registration", "registered", "land registry", "registrar"],
            "patterns": [r"regist(er|ration|ered)", r"land\s+registry"],
            "nli_premise": "Land sale deeds must be registered in the Land Registry."
        }
    ],

    # ========== ELECTRONIC CONTRACT / E-COMMERCE DOMAIN ==========
    "electronic_contract": [
        {
            "id": "econtract_parties",
            "name": "Identification of Parties",
            "description": "Parties must be clearly identified in electronic contracts",
            "legal_basis": "Electronic Transactions Act, No. 19 of 2006",
            "keywords": ["party", "parties", "service provider", "user", "customer", "merchant"],
            "patterns": [r"(party|parties)", r"(provider|user|customer|merchant)"],
            "nli_premise": "Electronic contracts must clearly identify all parties."
        },
        {
            "id": "consent_mechanism",
            "name": "Consent/Acceptance Mechanism",
            "description": "How consent is obtained (click-wrap, opt-in etc.)",
            "legal_basis": "Electronic Transactions Act, No. 19 of 2006",
            "keywords": ["consent", "accept", "agree", "click", "opt-in", "check box", "terms"],
            "patterns": [r"(consent|accept|agree)", r"(click|opt.?in|check.?box)"],
            "nli_premise": "Electronic contracts must include a clear consent mechanism."
        },
        {
            "id": "esignature_provision",
            "name": "Electronic Signature",
            "description": "Electronic signature validity",
            "legal_basis": "Electronic Transactions Act, No. 19 of 2006",
            "keywords": ["electronic signature", "e-signature", "digital signature", "electronically signed"],
            "patterns": [r"(electronic|digital)\s+signature", r"e-signature"],
            "nli_premise": "Electronic contracts should reference valid electronic signature mechanisms."
        },
        {
            "id": "terms_accessibility",
            "name": "Terms Accessibility",
            "description": "Terms must be accessible and readable",
            "legal_basis": "Electronic Transactions Act, No. 19 of 2006",
            "keywords": ["terms", "conditions", "accessible", "readable", "available", "displayed"],
            "patterns": [r"terms\s+(and|&)\s+conditions", r"(accessible|available|displayed)"],
            "nli_premise": "Electronic contract terms must be accessible and readable to users."
        },
        {
            "id": "dispute_resolution_ecommerce",
            "name": "Dispute Resolution",
            "description": "How disputes will be resolved",
            "legal_basis": "Electronic Transactions Act, No. 19 of 2006",
            "keywords": ["dispute", "resolution", "arbitration", "jurisdiction", "governing law"],
            "patterns": [r"dispute\s+resolut", r"(arbitration|jurisdiction|governing\s+law)"],
            "nli_premise": "Electronic contracts must include dispute resolution provisions."
        }
    ],
    
    "general": [
        {
            "id": "parties",
            "name": "Parties Identification",
            "description": "Names and details of all parties",
            "legal_basis": "Prevention of Frauds Ordinance",
            "keywords": ["party", "parties", "between", "hereinafter", "first party", "second party"],
            "patterns": [r"(first|second)\s+party", r"between.*and", r"hereinafter"],
            "nli_premise": "Contracts must clearly identify all parties involved."
        },
        {
            "id": "terms",
            "name": "Terms & Conditions",
            "description": "Main terms of the agreement",
            "legal_basis": "Prevention of Frauds Ordinance",
            "keywords": ["terms", "conditions", "agreement", "covenant", "undertake", "agree"],
            "patterns": [r"terms\s+(and|&)\s+conditions", r"(covenant|agree|undertake)"],
            "nli_premise": "Contracts must include clear terms and conditions."
        },
        {
            "id": "signatures",
            "name": "Signatures",
            "description": "Signature requirements",
            "legal_basis": "Prevention of Frauds Ordinance",
            "keywords": ["signature", "signed", "sign", "witness", "executed"],
            "patterns": [r"sign(ed|ature)?", r"witness(ed)?", r"execut(ed|ion)"],
            "nli_premise": "Contracts must be properly signed by all parties."
        }
    ]
}


def check_mandatory_clauses_hybrid(contract_text, domain):
    """
    HYBRID APPROACH: Rule-Based Detection + NLI Verification
    
    Stage 1: Fast keyword/regex matching
    Stage 2: NLI verification using trained model (optional for high-confidence matches)
    
    Returns: {"present": [...], "missing": [...]}
    """
    contract_lower = contract_text.lower()
    present = []
    missing = []
    
    # Get mandatory clauses for this domain
    mandatory_clauses = MANDATORY_CLAUSES.get(domain, MANDATORY_CLAUSES.get("general", []))
    
    for clause_def in mandatory_clauses:
        clause_id = clause_def["id"]
        clause_name = clause_def["name"]
        keywords = clause_def["keywords"]
        patterns = clause_def.get("patterns", [])
        legal_basis = clause_def["legal_basis"]
        nli_premise = clause_def.get("nli_premise", "")
        
        # STAGE 1: Rule-Based Detection (Keyword + Regex)
        keyword_score = 0
        matched_keywords = []
        
        # Check keywords
        for kw in keywords:
            if kw in contract_lower:
                keyword_score += 1
                matched_keywords.append(kw)
        
        # Check regex patterns
        pattern_matched = False
        for pattern in patterns:
            if re.search(pattern, contract_lower, re.IGNORECASE):
                pattern_matched = True
                keyword_score += 2  # Patterns get higher weight
                break
        
        # Calculate initial confidence based on rule matching
        max_possible_score = len(keywords) + 2  # All keywords + pattern match
        rule_confidence = min((keyword_score / max_possible_score) * 100, 100) if max_possible_score > 0 else 0
        
        # STAGE 2: NLI Verification (for borderline cases)
        nli_verified = False
        nli_confidence = 0
        
        if keyword_score >= 1:  # At least one keyword found
            # Try NLI verification if we have a premise
            if nli_premise and len(matched_keywords) > 0:
                try:
                    # Find the relevant clause text containing the keywords
                    relevant_text = extract_relevant_text(contract_text, matched_keywords)
                    if relevant_text:
                        nli_result = predict(nli_premise, relevant_text)
                        if nli_result["label_id"] == 0 or "entailment" in nli_result.get("status", "").lower():
                            nli_verified = True
                            nli_confidence = nli_result["confidence"]
                except Exception:
                    # If NLI fails, rely on rule-based confidence
                    pass
        
        # Final decision: combine rule-based and NLI results
        if keyword_score >= 2 or pattern_matched:
            # Strong match from rules
            final_confidence = rule_confidence
            if nli_verified:
                final_confidence = max(rule_confidence, nli_confidence)
            
            present.append({
                "id": clause_id,
                "clause": clause_name,
                "legal_basis": legal_basis,
                "confidence": round(final_confidence, 1),
                "matched_keywords": matched_keywords[:5],  # Limit to 5
                "nli_verified": nli_verified
            })
        elif keyword_score == 1 and nli_verified:
            # Weak rule match but NLI confirms
            present.append({
                "id": clause_id,
                "clause": clause_name,
                "legal_basis": legal_basis,
                "confidence": round(nli_confidence, 1),
                "matched_keywords": matched_keywords,
                "nli_verified": True
            })
        else:
            # Missing clause
            missing.append({
                "id": clause_id,
                "clause": clause_name,
                "legal_basis": legal_basis,
                "rule": f"Document should contain {clause_name} clause as per {legal_basis}",
                "confidence": 0
            })
    
    return {"present": present, "missing": missing}


def extract_relevant_text(contract_text, keywords, context_size=200):
    """Extract text around matched keywords for NLI verification"""
    contract_lower = contract_text.lower()
    
    for kw in keywords:
        pos = contract_lower.find(kw)
        if pos != -1:
            start = max(0, pos - context_size)
            end = min(len(contract_text), pos + len(kw) + context_size)
            return contract_text[start:end]
    
    return None


def check_mandatory_clauses(contract_text, domain):
    """
    Main function for mandatory clause checking.
    Uses Hybrid approach (Rule-Based + NLI Verification).
    Returns only missing clauses for backward compatibility.
    """
    result = check_mandatory_clauses_hybrid(contract_text, domain)
    return result["missing"]


def get_nli_confidence(clause, rule_text):
    """Get actual NLI model confidence score for a clause-rule pair"""
    try:
        nli_result = predict(rule_text, clause)
        return nli_result["confidence"], nli_result["label_id"], nli_result.get("all_probs", {})
    except Exception:
        return 75.0, 1, {}  # Fallback to default


def check_compliance(contract_text):
    """Main compliance checking function with real NLI confidence scores"""
    domain = detect_domain(contract_text)
    clauses = split_into_clauses(contract_text)
    
    report = {
        "domain": domain,
        "document_type": domain,
        "clauses": [],
        "present_mandatory": [],
        "missing_mandatory": []
    }
    
    # Get domain-specific patterns + general patterns
    illegal_patterns = ILLEGAL_PATTERNS.get(domain, []) + GENERAL_ILLEGAL_PATTERNS
    legal_patterns = LEGAL_PATTERNS.get(domain, [])
    
    for clause in clauses:
        # Skip administrative clauses
        if is_administrative_clause(clause):
            continue
        
        category, config = classify_clause(clause, domain)
        
        if config.get("ignore", False):
            continue
        
        # Check ILLEGAL patterns first
        illegal_match = check_pattern_match(clause, illegal_patterns)
        
        if illegal_match:
            # Get actual NLI confidence for illegal matches
            nli_confidence, label_id, all_probs = get_nli_confidence(clause, illegal_match["rule"])
            # Use NLI confidence, ensure minimum 85% for pattern-matched violations
            final_confidence = max(nli_confidence, 85.0) if label_id == 0 else nli_confidence
            
            report["clauses"].append({
                "clause": clause,
                "status": "🔴 Violation",
                "prediction": "contradiction",
                "violated_act": illegal_match["act"],
                "section": illegal_match["section"],
                "law_reference": f"{illegal_match['act']} Section {illegal_match['section']}",
                "matched_rule": illegal_match["rule"],
                "confidence": round(final_confidence, 1),
                "recommendation": illegal_match["recommendation"],
                "category": category
            })
            continue
        
        # Check LEGAL patterns
        legal_match = check_pattern_match(clause, legal_patterns)
        
        if legal_match:
            # Get actual NLI confidence for legal matches
            nli_confidence, label_id, all_probs = get_nli_confidence(clause, legal_match["rule"])
            
            report["clauses"].append({
                "clause": clause,
                "status": "🟢 Compliant",
                "prediction": "entailment",
                "violated_act": None,
                "section": legal_match["section"],
                "law_reference": f"{legal_match['act']} Section {legal_match['section']}",
                "matched_rule": legal_match["rule"],
                "confidence": round(nli_confidence, 1),
                "recommendation": legal_match["recommendation"],
                "category": category
            })
            continue
        
        # For remaining clauses - provide law reference based on category
        category_law = get_category_law_info(category, domain)
        # Get actual NLI confidence for category-based matches
        nli_confidence, label_id, all_probs = get_nli_confidence(clause, category_law["rule"])
        
        report["clauses"].append({
            "clause": clause,
            "status": "🟢 Compliant",
            "prediction": "entailment",
            "violated_act": None,
            "section": category_law["section"],
            "law_reference": f"{category_law['act']} Section {category_law['section']}",
            "matched_rule": category_law["rule"],
            "confidence": round(nli_confidence, 1),
            "recommendation": f"COMPLIANT: {category_law['rule']}",
            "category": category
        })
    
    # Get mandatory clause analysis using Hybrid approach
    mandatory_result = check_mandatory_clauses_hybrid(contract_text, domain)
    report["present_mandatory"] = mandatory_result["present"]
    report["missing_mandatory"] = mandatory_result["missing"]
    
    return report
