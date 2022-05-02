import textwrap

def run_python_package_import_test(test_case, schema, language_alias, pkg, language_alias, fail=False, alternative=None):
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
    print(sql)
    test_case.query(sql)
    try:
        rows = test_case.query(f'''SELECT {schema}.test_import_of_package() FROM dual''')
        if not fail:
            test_case.assertRowsEqual([(None,)], rows)
        else:
            assert 'Expected Failure' == 'not found'
    except:
        if fail:
            return
        if alternative:
            run_python_package_import_test(test_case, alternative, language_alias, fail)
        else:
            raise
