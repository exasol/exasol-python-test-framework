"""UDF package availability helpers."""
# pylint: disable=C0114,C0115,C0116,C0301,C0303,C0305,C0411,C0103,C0209,C0204,C0415,R1705,R1710,R1720,R1732,R0205,R0903,R0911,R0912,R0913,R0917,R1725,W0201,W0212,W0231,W0238,W0511,W0603,W0611,W0612,W0622,W0702,W0718,W0719,W1201,W1202,W1514,I1101

import textwrap

def run_python_package_import_test(test_case, schema, language_alias, pkg, fail=False, alternative=None):
    sql=textwrap.dedent(f'''
        CREATE OR REPLACE {language_alias} SCALAR SCRIPT {schema}.test_import_of_package() returns VARCHAR(2000000) AS
        
        def run(ctx):
            try:
                import {pkg}
            except Exception as e:
                import traceback
                return traceback.format_exc()
            return None
        /
        ''')
    test_case.query(sql)
    try:
        rows = test_case.query(f'''SELECT {schema}.test_import_of_package() FROM dual''')
        if not fail:
            test_case.assertRowsEqual([(None,)], rows)
        else:
            test_case.fail('Failure was expected')
    except:
        if fail:
            return
        if alternative:
            run_python_package_import_test(test_case, schema, language_alias, alternative, fail)
        else:
            raise
