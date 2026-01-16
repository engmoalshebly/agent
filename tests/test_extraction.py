from app.engine.professional_engine import professional_engine

test_messages = [
    "اسمي محمد القحطاني، ورقم هويتي 1023456789 وتاريخ ميلادي 1990-05-15",
    "عندي تويوتا كامري موديل 2022، قيمتها تقريباً 90 الف ورقم اللوحة أ ب ج 1234",
    "سيارتي هيونداي سوناتا 2021 لوحة ج د ه 4567 قيمتها 80000"
]

for msg in test_messages:
    data = professional_engine._extract_all_data(msg)
    print(f"Message: {msg}")
    print(f"Extracted: {data}")
    print("-" * 20)

# Test plate extraction specifically
plate_msg = "رقم اللوحة أ ب ج 1234"
plate = professional_engine._extract_plate(plate_msg)
print(f"Plate test: '{plate_msg}' -> '{plate}'")

# Test year extractions
year_msgs = ["موديل 2022", "سنة 2020", "2021،", "من 2018"]
for ym in year_msgs:
    y = professional_engine._extract_year(ym)
    print(f"Year test: '{ym}' -> '{y}'")

# Test price extractions
price_msgs = ["90 الف", "85000 ريال", "قيمتها 100000", "50,000"]
for pm in price_msgs:
    p = professional_engine._extract_price(pm)
    print(f"Price test: '{pm}' -> '{p}'")
