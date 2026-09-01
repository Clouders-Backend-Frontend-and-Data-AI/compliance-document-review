import json
import os
import sys
import random
from datetime import datetime, timezone, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, Base, engine
from app.models.vector_corpus import ComplianceRule, PrecedentSubmission
from app.models.user import User
from app.models.base import RuleCategory, DocumentStatus, DocumentType, UserRole
from app.core.security import get_password_hash
from app.services.vector_engine import VectorEngine
from app.services.pii_masker import PIIMasker

RULES_DATA = [
    # Required Disclosures
    {
        "rule_code": "SEC-MKT-01",
        "category": RuleCategory.REQUIRED_DISCLOSURE,
        "title": "General Risk of Loss & Past Performance Disclaimer",
        "description": "Mandatory disclaimer stating that past performance is not indicative of future results and investing involves risk of loss.",
        "rule_text": "All marketing materials referencing investment strategies or returns must include a clear disclosure stating that past performance does not guarantee future results and that investing in securities involves risk, including possible loss of principal.",
        "standard_disclosure": "Past performance is not indicative of future results. Investing in securities involves risk of loss that clients should be prepared to bear."
    },
    {
        "rule_code": "SEC-MKT-02",
        "category": RuleCategory.REQUIRED_DISCLOSURE,
        "title": "SEC/RIA Registration Status Notice",
        "description": "Disclosure clarifying that registration with the SEC or state regulator does not imply a certain level of skill or training.",
        "rule_text": "Communications stating RIA registration must clarify that SEC registration does not constitute an endorsement or imply specialized government accreditation.",
        "standard_disclosure": "Registration with the SEC or any state securities authority does not imply a certain level of skill or training."
    },
    {
        "rule_code": "BANK-DISC-01",
        "category": RuleCategory.REQUIRED_DISCLOSURE,
        "title": "Not FDIC Insured / No Bank Guarantee Notice",
        "description": "Mandatory disclosure when distributing investment materials through or alongside banking institutions.",
        "rule_text": "Non-deposit investment products must clearly disclose: Not FDIC Insured, May Lose Value, No Bank Guarantee.",
        "standard_disclosure": "Investment products are: NOT FDIC INSURED | MAY LOSE VALUE | NOT BANK GUARANTEED."
    },
    {
        "rule_code": "TAX-DISC-01",
        "category": RuleCategory.REQUIRED_DISCLOSURE,
        "title": "Tax and Legal Advice Disclaimer",
        "description": "Disclaimer indicating that the advisor does not provide tax, legal, or accounting advice.",
        "rule_text": "Any discussion of tax strategies or estate planning structures must advise clients to consult independent legal or CPA counsel.",
        "standard_disclosure": "This material has been prepared for informational purposes only and does not constitute tax, legal, or accounting advice. Please consult your personal CPA or attorney."
    },
    {
        "rule_code": "FEE-DISC-01",
        "category": RuleCategory.REQUIRED_DISCLOSURE,
        "title": "Advisory Fee & Expense Schedule Disclosure",
        "description": "Requirement to clearly state that advisory fees, custodial costs, and underlying fund expenses will reduce investor net returns.",
        "rule_text": "Communications referencing portfolio management must state that advisory fees apply and will impact cumulative returns over time.",
        "standard_disclosure": "Advisory services are subject to an annual management fee as described in Form ADV Part 2A. Underlying fund fees and trading costs apply."
    },
    {
        "rule_code": "SEC-TEST-01",
        "category": RuleCategory.REQUIRED_DISCLOSURE,
        "title": "Testimonial and Endorsement Disclosure",
        "description": "Mandatory disclosures when utilizing client reviews, testimonials, or third-party endorsements under SEC Marketing Rule.",
        "rule_text": "Testimonials must disclose whether the speaker is a client, whether cash or non-cash compensation was provided, and any material conflicts of interest.",
        "standard_disclosure": "Testimonial given by an active client. No compensation was provided. Individual experiences may vary and do not guarantee future client success."
    },
    {
        "rule_code": "HYPO-DISC-01",
        "category": RuleCategory.REQUIRED_DISCLOSURE,
        "title": "Hypothetical & Backtested Illustration Disclosure",
        "description": "Disclosures regarding assumptions, methodology, and limitations of simulated or backtested performance models.",
        "rule_text": "Hypothetical returns must disclose all material assumptions, calculation methodology, and that simulated models do not represent actual trading.",
        "standard_disclosure": "Hypothetical results are simulated and have inherent limitations. Backtested models do not represent actual account trading and cannot account for economic or market risk."
    },
    {
        "rule_code": "SOCIAL-DISC-01",
        "category": RuleCategory.REQUIRED_DISCLOSURE,
        "title": "Social Media & Public Forum Notice",
        "description": "Required link or statement pointing to firm ADV brochure on public social posts.",
        "rule_text": "Public social media posts promoting advisory services must provide direct access to firm disclosures and Form CRS.",
        "standard_disclosure": "For full regulatory disclosures and our Form CRS, please visit our website at [WEBSITE_URL]."
    },
    {
        "rule_code": "RATING-DISC-01",
        "category": RuleCategory.REQUIRED_DISCLOSURE,
        "title": "Third-Party Rating / Award Methodology Disclosure",
        "description": "Disclosures for awards, rankings (e.g. Forbes, Barron's, Financial Times).",
        "rule_text": "Any mention of advisor awards or rankings must disclose the awarding entity, criteria used, date range, and whether the advisor paid a participation fee.",
        "standard_disclosure": "Rankings based on quantitative and qualitative criteria by third-party publisher. Advisor did not pay a fee to participate."
    },
    {
        "rule_code": "CONFLICT-DISC-01",
        "category": RuleCategory.REQUIRED_DISCLOSURE,
        "title": "Conflict of Interest & Affiliated Products Notice",
        "description": "Disclosure of proprietary funds or revenue sharing arrangements.",
        "rule_text": "If materials recommend proprietary products or arrangements involving 12b-1 fees, conflicts of interest must be disclosed prominently.",
        "standard_disclosure": "Advisors may recommend affiliated funds. Full details on compensation and conflict mitigation are outlined in Form ADV."
    },

    # Prohibited Claims
    {
        "rule_code": "SEC-PROH-01",
        "category": RuleCategory.PROHIBITED_CLAIMS,
        "title": "Absolute Guarantee of Principal or Returns",
        "description": "Strict prohibition against guaranteeing investment gains or safety of principal.",
        "rule_text": "Advisors are strictly prohibited from stating or implying that any security, portfolio, or strategy is 'guaranteed', 'risk-free', '100% safe', or 'insured against loss'.",
        "standard_disclosure": None
    },
    {
        "rule_code": "SEC-PROH-02",
        "category": RuleCategory.PROHIBITED_CLAIMS,
        "title": "Misleading Superlatives & Exaggerated Claims",
        "description": "Ban on unsubstantiated superlatives such as 'the best fund', 'unmatched wealth building', 'can't lose'.",
        "rule_text": "Marketing materials must be fair and balanced. Communications cannot use sensationalized or unverifiable promotional statements regarding performance.",
        "standard_disclosure": None
    },
    {
        "rule_code": "SEC-PROH-03",
        "category": RuleCategory.PROHIBITED_CLAIMS,
        "title": "Cherry-Picked or Selective Time Periods",
        "description": "Prohibition against selecting isolated profitable quarters while ignoring corresponding down periods.",
        "rule_text": "Performance cannot be selectively presented for favorable anomalous timeframes without providing full standard multi-year context.",
        "standard_disclosure": None
    },
    {
        "rule_code": "SEC-PROH-04",
        "category": RuleCategory.PROHIBITED_CLAIMS,
        "title": "Implied SEC or Government Endorsement",
        "description": "Prohibition of language suggesting regulatory agency validation or approval of investment acumen.",
        "rule_text": "No communication may represent or imply that the SEC, FINRA, or state regulator has approved or endorsed an advisor's abilities or portfolios.",
        "standard_disclosure": None
    },
    {
        "rule_code": "SEC-PROH-05",
        "category": RuleCategory.PROHIBITED_CLAIMS,
        "title": "Omission of Material Downside Risk",
        "description": "Promoting upside gains without proportionate discussion of downside volatility and potential loss.",
        "rule_text": "Communications highlighting high yields or growth potential must give equal prominence to the corresponding risks and market conditions.",
        "standard_disclosure": None
    },
    {
        "rule_code": "SEC-PROH-06",
        "category": RuleCategory.PROHIBITED_CLAIMS,
        "title": "Unapproved Third-Party Testimonials",
        "description": "Publishing unvetted customer quotes or fabricating client endorsements.",
        "rule_text": "Testimonials cannot be published without written client consent, conflict verification, and compliance officer pre-clearance.",
        "standard_disclosure": None
    },
    {
        "rule_code": "SEC-PROH-07",
        "category": RuleCategory.PROHIBITED_CLAIMS,
        "title": "Promises of Target Income or Dividend Continuance",
        "description": "Presenting dividends or yields as fixed obligations rather than discretionary distributions.",
        "rule_text": "Dividends and yields must not be described as guaranteed or permanent, as corporate boards may alter distributions at any time.",
        "standard_disclosure": None
    },

    # Performance Standards
    {
        "rule_code": "PERF-STD-01",
        "category": RuleCategory.PERFORMANCE_STANDARDS,
        "title": "Net-of-Fees Presentation Requirement",
        "description": "All presented performance must be shown net of maximum advisory fees and expenses or alongside gross returns with equal prominence.",
        "rule_text": "Under the SEC Marketing Rule, gross performance may not be displayed in advertisements without displaying net performance with at least equal prominence and over the same time periods.",
        "standard_disclosure": "Returns presented net of maximum advisory fee of 1.00% and reflect reinvestment of dividends and capital gains."
    },
    {
        "rule_code": "PERF-STD-02",
        "category": RuleCategory.PERFORMANCE_STANDARDS,
        "title": "Standardized Multi-Period Performance (1, 5, 10 Year)",
        "description": "Requirement to show 1-year, 5-year, and 10-year (or since inception) cumulative and annualized returns ending on the most recent calendar quarter.",
        "rule_text": "Performance must cover standardized 1, 5, and 10-year time horizons (or since inception) through the most recent calendar quarter-end.",
        "standard_disclosure": "Performance data shown through December 31, 2023. Periods greater than one year are annualized."
    },
    {
        "rule_code": "PERF-STD-03",
        "category": RuleCategory.PERFORMANCE_STANDARDS,
        "title": "Appropriate Benchmark Comparison",
        "description": "Performance comparisons must compare against a relevant, broad-based market index reflecting the strategy's risk profile.",
        "rule_text": "Comparisons to an index (e.g. S&P 500) must disclose the nature of the benchmark, including dividend treatment and risk differentials.",
        "standard_disclosure": "Benchmark index is unmanaged and does not reflect transaction costs or advisory fees. Direct investment in an index is not possible."
    },
    {
        "rule_code": "PERF-STD-04",
        "category": RuleCategory.PERFORMANCE_STANDARDS,
        "title": "Predecessor Performance Attribution",
        "description": "Standards for carrying over track records from prior advisory firms.",
        "rule_text": "Predecessor performance requires substantiation that the advising personnel were primarily responsible for the track record at the prior entity.",
        "standard_disclosure": "Performance achieved at predecessor firm by managing committee under substantially similar investment mandate."
    },
    {
        "rule_code": "PERF-STD-05",
        "category": RuleCategory.PERFORMANCE_STANDARDS,
        "title": "Extracted Performance Rules",
        "description": "Standards for highlighting a subset of investments from a multi-asset strategy.",
        "rule_text": "Extracted performance of a single asset class or sleeve must provide or offer to provide the entire portfolio's performance.",
        "standard_disclosure": "Extracted sleeve performance shown. Full composite returns available upon request."
    },

    # Supervision
    {
        "rule_code": "SUPV-01",
        "category": RuleCategory.SUPERVISION,
        "title": "Prior Written Approval for Retail Communications",
        "description": "All client-facing brochures, blast emails, and advertisements require pre-approval by a designated Compliance Officer.",
        "rule_text": "No retail communication may be published, mailed, or sent electronically without documented prior approval from the firm's compliance team.",
        "standard_disclosure": None
    },
    {
        "rule_code": "SUPV-02",
        "category": RuleCategory.SUPERVISION,
        "title": "Advertising Recordkeeping (SEC Rule 204-2)",
        "description": "Requirement to archive all disseminated marketing materials, substantiation files, and review decisions for 5 years.",
        "rule_text": "Advisors must maintain complete records of all advertisements, calculation worksheets, and compliance approval logs.",
        "standard_disclosure": None
    },
    {
        "rule_code": "SUPV-03",
        "category": RuleCategory.SUPERVISION,
        "title": "Suitability & Target Market Verification",
        "description": "Ensuring material is appropriate for the intended recipient audience (retail vs institutional).",
        "rule_text": "Materials targeting retail investors must use plain language and avoid complex derivative concepts unless accompanied by comprehensive risk education.",
        "standard_disclosure": None
    }
]

SAMPLE_PRECEDENT_TEMPLATES = [
    # Approved Precedents
    {
        "title": "Q3 2024 Market Outlook & Macro Trends Newsletter",
        "type": DocumentType.BROCHURE,
        "decision": DocumentStatus.APPROVED,
        "comment": "Well-balanced macro summary. Appropriate standard 1/5/10-yr benchmarks included. Mandatory risk and tax disclaimers clearly visible in footer.",
        "text": "Dear [CLIENT_1],\n\nWe are pleased to provide our Q3 2024 Market Outlook. Over the past quarter, global equity markets experienced moderate expansion driven by corporate earnings resilience.\n\nOur Moderate Growth Portfolio generated a 1-year annualized return of 8.4% and a 5-year return of 7.1% (net of 1.00% advisory fees), compared to the S&P 500 TR index return of 9.2% and 8.1% over the same periods.\n\nDisclosures:\nPast performance is not indicative of future results. Investing in securities involves risk of loss that clients should be prepared to bear. This material is for informational purposes only and does not constitute tax or legal advice. Registration with the SEC does not imply a certain level of skill or training."
    },
    {
        "title": "Retirement Transition & Social Security Planning Guide",
        "type": DocumentType.BROCHURE,
        "decision": DocumentStatus.APPROVED,
        "comment": "Excellent educational piece. Contains all required tax and CPA consultation disclaimers. No promissory claims made.",
        "text": "Planning Your Retirement Transition\nPrepared for: [CLIENT_2]\n\nTransitioning into retirement requires a comprehensive assessment of income streams, retirement account distributions (401k/IRA), and tax implications.\n\nKey Considerations:\n1. Evaluating withdrawal rates based on historical longevity models.\n2. Coordinating Social Security claiming strategies.\n3. Asset location across taxable, tax-deferred, and Roth accounts.\n\nDisclaimer: This guide is prepared for informational purposes only and does not constitute tax, legal, or accounting advice. Please consult your personal CPA or tax attorney."
    },
    {
        "title": "Wealth Management Overview for New Family Clients",
        "type": DocumentType.PROPOSAL_LETTER,
        "decision": DocumentStatus.APPROVED,
        "comment": "Approved. Clear fee schedule outlined in accordance with Form ADV Part 2A. Mandatory risk disclosures present.",
        "text": "Dear [CLIENT_3],\n\nThank you for meeting with our advisory team regarding your long-term wealth management goals. Our firm provides fee-only fiduciary financial planning and asset management.\n\nOur fee schedule is tiered starting at 0.85% for assets under management, billed quarterly in arrears.\n\nInvestment products are: NOT FDIC INSURED | MAY LOSE VALUE | NOT BANK GUARANTEED. Past performance is not indicative of future results."
    },

    # Rejected Precedents
    {
        "title": "Guaranteed High-Yield AI Strategy Social Post",
        "type": DocumentType.SOCIAL_POST,
        "decision": DocumentStatus.REJECTED,
        "comment": "Rejected. Blatant promissory language ('guaranteed 18% yield', 'risk-free'). Lacks all mandatory risk disclosures. Unacceptable for publication.",
        "text": "Want to earn guaranteed returns? Our new AI Algorithmic Momentum Strategy delivers a guaranteed 18% annual return with zero risk of downside! Don't let market crashes hurt your savings. Sign up today and watch your money double!"
    },
    {
        "title": "Exclusive Tech Sleeve Outperformance Blast Email",
        "type": DocumentType.MARKETING_EMAIL,
        "decision": DocumentStatus.REJECTED,
        "comment": "Rejected. Cherry-picked 3-month performance (+45%) with no 1/5/10-year standardized figures and no net-of-fees disclosure. Grossly unbalanced.",
        "text": "Hello [CLIENT_4],\n\nOur Tech Sleeve was up +45% in Q2! Our managers consistently pick the highest returning stocks in the entire market. Join our proprietary fund now before spots run out.\nContact [EMAIL_1] or call [PHONE_1]."
    },
    {
        "title": "Client Video Endorsement Promotion",
        "type": DocumentType.SOCIAL_POST,
        "decision": DocumentStatus.REJECTED,
        "comment": "Rejected. Uses client testimonial without required SEC Marketing Rule disclosure regarding compensation and conflict of interest.",
        "text": "Listen to what [CLIENT_5] says: 'This advisory team made me $500k in 1 year! They are the best in the state!' Watch the full video interview on our page."
    },

    # Needs Revision Precedents
    {
        "title": "Comprehensive Municipal Bond Strategy Proposal",
        "type": DocumentType.PROPOSAL_LETTER,
        "decision": DocumentStatus.NEEDS_REVISION,
        "comment": "Needs Revision: Please add standard Tax Advice Disclaimer in the footer since tax-exempt interest is discussed. Also clarify gross vs net returns.",
        "text": "Prepared for: [CLIENT_6]\nAccount Number: [ACCOUNT_1]\n\nOur Municipal Bond Strategy seeks to deliver federal tax-exempt income by investing in investment-grade state and municipal obligations. Current strategy yield is 4.2%.\n\nPast performance is not indicative of future results. Investing in securities involves risk of loss."
    },
    {
        "title": "Q4 ESG Sustainability Portfolio Brochure",
        "type": DocumentType.BROCHURE,
        "decision": DocumentStatus.NEEDS_REVISION,
        "comment": "Needs Revision: Please update the benchmark comparison to show 1-year, 5-year, and 10-year annualized periods instead of just the YTD figure.",
        "text": "ESG Core Growth Portfolio\nPrepared by Advisor: [CLIENT_7]\n\nThe ESG Core Growth Strategy invests in companies with leading environmental and governance practices. YTD performance is +11.2% versus +9.8% for the ESG Leaders Index.\n\nDisclosures: Past performance does not guarantee future results. Advisory fees apply."
    },
    {
        "title": "Executive Equity Compensation & RSU Advisory Memo",
        "type": DocumentType.MEETING_NOTES,
        "decision": DocumentStatus.NEEDS_REVISION,
        "comment": "Needs Revision: Must include SEC RIA Registration Status disclaimer and explicit recommendation to consult tax advisor regarding Section 83(b) elections.",
        "text": "Meeting Notes & Strategy Plan for [CLIENT_8]\n\nDiscussion regarding restricted stock unit (RSU) vesting schedules and diversification strategies. We discussed gradual liquidation upon vesting to reduce concentration risk in employer equity."
    }
]

def seed_database():
    print("Starting database seeding...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Default Users
        advisor_user = db.query(User).filter(User.email == "advisor@example.com").first()
        if not advisor_user:
            advisor_user = User(
                email="advisor@example.com",
                hashed_password=get_password_hash("Advisor123!"),
                full_name="Sarah Jenkins (Senior Advisor)",
                role=UserRole.ADVISOR
            )
            db.add(advisor_user)

        officer_user = db.query(User).filter(User.email == "officer@example.com").first()
        if not officer_user:
            officer_user = User(
                email="officer@example.com",
                hashed_password=get_password_hash("Officer123!"),
                full_name="David Vance (Chief Compliance Officer)",
                role=UserRole.OFFICER
            )
            db.add(officer_user)

        db.commit()
        print("Default users verified (advisor@example.com, officer@example.com).")

        # 2. Seed Compliance Rules
        print("Seeding Compliance Rules and Mandatory Disclosures...")
        existing_codes = {r.rule_code for r in db.query(ComplianceRule.rule_code).all()}
        
        for r_data in RULES_DATA:
            if r_data["rule_code"] not in existing_codes:
                embedding_text = r_data["rule_text"] + " " + r_data["title"]
                if r_data.get("standard_disclosure"):
                    embedding_text += " " + r_data["standard_disclosure"]
                vec = VectorEngine.generate_embedding(embedding_text)
                
                rule_obj = ComplianceRule(
                    rule_code=r_data["rule_code"],
                    category=r_data["category"],
                    title=r_data["title"],
                    description=r_data["description"],
                    rule_text=r_data["rule_text"],
                    standard_disclosure=r_data.get("standard_disclosure"),
                    embedding_json=json.dumps(vec)
                )
                db.add(rule_obj)
        db.commit()
        total_rules = db.query(ComplianceRule).count()
        print(f"Total compliance rules in database: {total_rules}")

        # 3. Seed ~100 Precedent Submissions for Rich Vector Search
        print("Seeding ~100 Precedent Submissions for vector similarity search...")
        current_precedents = db.query(PrecedentSubmission).count()
        
        if current_precedents < 80:
            doc_types = [
                DocumentType.MARKETING_EMAIL,
                DocumentType.BROCHURE,
                DocumentType.SOCIAL_POST,
                DocumentType.MEETING_NOTES,
                DocumentType.PROPOSAL_LETTER
            ]
            
            topics = [
                ("Small Cap Value Opportunity", "Equities", 1),
                ("Dividend Aristocrats Portfolio", "Income", 2),
                ("Tax-Advantaged Municipal Bonds", "Fixed Income", 3),
                ("Tech Disruption Growth Sleeve", "Sector", 4),
                ("Global Macro Strategic Allocation", "Multi-Asset", 5),
                ("Roth IRA Conversion Checklist", "Retirement", 6),
                ("Estate and Trust Wealth Preservation", "Wealth Planning", 7),
                ("Private Credit & Real Estate Direct", "Alternatives", 8),
                ("AI & Robotics ETF Strategy", "Thematic", 9),
                ("Ultra High Net Worth Family Office Brief", "HNW", 10)
            ]

            decisions_pool = [
                (DocumentStatus.APPROVED, "Approved. Contains standard 1/5/10 yr performance net of fees and mandatory disclaimers."),
                (DocumentStatus.APPROVED, "Approved for retail dissemination. Clean disclosure placement and balanced risk presentation."),
                (DocumentStatus.NEEDS_REVISION, "Needs Revision: Please add mandatory Tax Advice Disclaimer and SEC RIA registration disclaimer."),
                (DocumentStatus.NEEDS_REVISION, "Needs Revision: Missing standard benchmark multi-year performance comparison in table 2."),
                (DocumentStatus.REJECTED, "Rejected: Contains promissory language and fails to disclose underlying fund expenses."),
                (DocumentStatus.REJECTED, "Rejected: Unapproved testimonial references without compensation disclosure under SEC Rule 206(4)-1.")
            ]

            # Generate variations
            count = 0
            for idx in range(1, 105):
                topic, cat, t_id = random.choice(topics)
                dtype = random.choice(doc_types)
                dec, comment_template = random.choice(decisions_pool)
                
                title = f"{topic} #{idx} - {dtype.value.replace('_', ' ').title()}"
                
                # Synthetic document text with masked PII placeholders
                client_id = random.randint(10, 99)
                acct_id = random.randint(100000, 999999)
                
                if dec == DocumentStatus.APPROVED:
                    disc = "Disclosures: Past performance is not indicative of future results. Investing involves risk including loss of principal. Not FDIC Insured. Consult CPA for tax advice."
                elif dec == DocumentStatus.NEEDS_REVISION:
                    disc = "Disclosures: Advisory fees apply. Past performance is no guarantee."
                else:
                    disc = "Guaranteed high returns with unmatched security and low market risk."

                text = f"Title: {title}\nPrepared for: [CLIENT_{client_id}]\nAccount: [ACCOUNT_{acct_id}]\n\n" \
                       f"This communication outlines our {topic} investment thesis for Q{((idx%4)+1)} 2024. " \
                       f"Our strategy focuses on disciplined asset allocation and risk-managed capital preservation.\n\n" \
                       f"Key points:\n" \
                       f"- Targeted allocation based on macroeconomic momentum.\n" \
                       f"- Fee schedule starting at 0.75% annually.\n\n" \
                       f"{disc}"

                vec = VectorEngine.generate_embedding(text[:3000])

                prec = PrecedentSubmission(
                    title=title,
                    document_type=dtype,
                    masked_text=text,
                    decision=dec,
                    officer_comment=f"{comment_template} (Precedent Ref #{idx})",
                    embedding_json=json.dumps(vec),
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180))
                )
                db.add(prec)
                count += 1

            db.commit()
            print(f"Successfully seeded {count} precedent submissions.")

        total_precedents = db.query(PrecedentSubmission).count()
        print(f"Total precedent submissions in vector store: {total_precedents}")
        print("Seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
