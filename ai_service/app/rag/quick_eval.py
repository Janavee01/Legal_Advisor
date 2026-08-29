# quick_eval.py
import json
from ai_service.app.rag.retrieval_test_cases import TEST_CASES  # adjust import
from ai_service.app.rag.eval import run_case

MISS_QUERIES = {
    "what rights do I have during police interrogation",
"can employer fire me without any notice in India",
"what safety measures must factories provide for workers",
"what is maximum working hours per day in factory",
"what to do if employer does not pay salary",
"who is eligible for provident fund under social security code",
"how is employee insurance provided under law",
"What happens if a child commits a crime in India?",
"Can a minor be tried as an adult in serious cases?",
"What rehabilitation is provided to juvenile offenders?",
"school teacher suspects child abuse what is legal duty to report",
"Is police required to register FIR in child abuse cases?",
"Can live-in partner file domestic violence complaint?",
"Does POSH Act apply to contractual workers and interns?",
"What happens if employer does not deposit PF contribution?",
"Will I get salary during maternity leave?",
"Are electronic documents like emails valid evidence in court?",
"Is CCTV footage accepted as legal proof in criminal cases?",
"How can I become legal guardian of a child in India?",
"Can a court appoint guardian without parents consent?",
"Who can file petition for child custody in court?",
"Can grandparents become legal guardians of a minor?",
"What are the legal requirements for a valid Hindu marriage?",
"Can I remarry without getting divorce first?",
"Is live-in relationship considered marriage under Hindu law?",
"What is a legal will and how do I make one valid?",
"What happens if there is no nominee in bank account after death?",
"Is handwritten will legally valid in India?",
"How can two people from different religions get married legally?",
"What is the procedure for registering marriage under Special Marriage Act?",
"Can I marry without religious ceremony under law?",
"Is it mandatory to register a sale deed in India?",
"What happens if I don't register a property sale agreement?",
"Can a gift deed be valid without registration?",
"does government provide lawyer for domestic violence victim",
"What information can I request under RTI Act?",
"Can government refuse to give information under RTI?",
"What can I do if my RTI request is ignored?",
"Where can senior citizens complain about neglect by children?",
"Can a company refuse job to a person because of disability?",
"What is considered an offence under SC/ST Atrocities Act?",
"unguarded machine caused worker injury in factory",
"maximum working hours per day in factory",
"repairs not done by landlord in rented property",
"bank auctioning mortgaged property after default",
"fake celebrity ad misled me into buying a product",
"who counts as a consumer under the act?",
"seller refused refund for defective item after purchase",
"internet provider is not providing promised service",
"product warranty was denied by the company",
"restaurant served spoiled food",
"worked extra hours but got normal salary only",
"drug addict seeking treatment instead of punishment",
"possessing or carrying firearm without licence",
"phishing or online banking fraud",
"Is driving without a license a punishable offence?",
"What happens if I drive without insurance?",
"How do I get a driving license in India?"
}

subset = [tc for tc in TEST_CASES if tc.query in MISS_QUERIES]
print(f"Re-testing {len(subset)} previous misses")

for tc in subset:
    outcome = run_case(tc, 5)