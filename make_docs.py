import os, csv, random
from core.llm import ask

# These prompts are committed on purpose: the assignment asks for the synthesis prompts.
HR_DOCS = {
    "leave_policy.txt": "Write a realistic company HR Leave Policy for a shipping company's shore staff. Include annual leave days, sick leave rules, maternity and paternity leave, carry-forward limits, and how to apply. Use specific numbers. About 350 words. Plain text, no markdown.",
    "code_of_conduct.txt": "Write a realistic Code of Conduct for shore staff of a shipping company. Include dress code, working hours, harassment reporting steps, conflict of interest, and use of company devices. Use specific numbers and timelines. About 350 words. Plain text, no markdown.",
    "travel_policy.txt": "Write a realistic Business Travel and Expense Policy for a shipping company. Include flight class rules, hotel limits per night in rupees, daily food allowance, claim deadline, and approvals needed. Use specific numbers. About 350 words. Plain text, no markdown.",
}
SHIP_DOCS = {
    "supplier_alpha.txt": "Write a supplier terms document for 'Alpha Marine Supplies' selling ship spare parts. Include payment terms, delivery times in days, warranty period, minimum order value in USD, return policy, and discounts for bulk orders. Use specific numbers. About 300 words. Plain text, no markdown.",
    "supplier_beta.txt": "Write a supplier terms document for 'Beta Ocean Traders' selling ship spare parts. Include payment terms, delivery times in days, warranty period, minimum order value in USD, urgent delivery surcharge, and return policy. Use specific numbers different from Alpha Marine. About 300 words. Plain text, no markdown.",
}

def write_docs(folder, docs):
    os.makedirs(folder, exist_ok=True)
    for name, prompt in docs.items():
        text = ask(prompt)
        open(os.path.join(folder, name), "w", encoding="utf-8").write(text)
        print("wrote", folder, name)

write_docs("demos/hr_policy/docs", HR_DOCS)
write_docs("demos/ship_spares/docs", SHIP_DOCS)

# catalogue CSV: random but fixed with a seed, so it is reproducible
random.seed(7)
parts = [("Fuel injector", 420), ("Piston ring set", 310), ("Turbocharger cartridge", 2850),
         ("Cylinder liner", 1190), ("Fuel pump", 760), ("Oil filter", 38), ("Air cooler", 1640),
         ("Exhaust valve", 295), ("Bearing shell", 175), ("Gasket kit", 85),
         ("Starting air valve", 530), ("Lube oil pump", 980), ("Thermostat valve", 140),
         ("Sea water pump seal", 62), ("Governor actuator", 2200)]
with open("demos/ship_spares/docs/catalogue.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["part_no", "part_name", "price_usd", "supplier", "stock", "lead_time_days"])
    for i, (name, price) in enumerate(parts):
        w.writerow([f"SP-{1000 + i}", name, price, random.choice(["Alpha Marine Supplies", "Beta Ocean Traders"]),
                    random.randint(0, 40), random.choice([3, 5, 7, 14, 21])])
print("wrote catalogue.csv")