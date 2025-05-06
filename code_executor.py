import subprocess
import os
import tempfile
import json
from typing import Dict, Tuple


def execute_python_code(code: str, test_cases: List[Dict]) -> Tuple[bool, str]:
    # Geçici bir dosya oluştur
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
        temp.write(code.encode('utf-8'))
        temp_path = temp.name

    results = []
    all_passed = True

    for test_case in test_cases:
        try:
            # Kodu çalıştır ve girişi ilet
            process = subprocess.run(
                ['python', temp_path],
                input=test_case['input'].encode(),
                capture_output=True,
                timeout=5  # 5 saniye timeout
            )

            # Çıktıyı al ve beklenenle karşılaştır
            output = process.stdout.decode().strip()
            if output == test_case['expected_output']:
                results.append(f"✅ Test passed: {test_case['description']}")
            else:
                results.append(
                    f"❌ Test failed: {test_case['description']}\nExpected: {test_case['expected_output']}\nGot: {output}")
                all_passed = False

        except subprocess.TimeoutExpired:
            results.append(f"⏱️ Timeout: {test_case['description']}")
            all_passed = False
        except Exception as e:
            results.append(f"⚠️ Error: {test_case['description']}\n{str(e)}")
            all_passed = False

    # Geçici dosyayı sil
    os.unlink(temp_path)

    return all_passed, "\n".join(results)