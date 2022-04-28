
def run_python_package_import_test(test_case, pkg, fail=False, alternative=None):
    sql=udf.fixindent('''
        CREATE OR REPLACE PYTHON3 SCALAR SCRIPT available_packages.test_import_of_package() returns VARCHAR(2000000) AS
        
        def run(ctx):
            try:
                import %s
            except Exception as e:
                import traceback
                return traceback.format_exc()
            return None
        /
        ''' % (pkg))
    print(sql)
    test_case.query(sql)
    try:
        rows = test_case.query('''SELECT available_packages.test_import_of_package() FROM dual''')
        if not fail:
            test_case.assertRowsEqual([(None,)], rows)
        else:
            assert 'Expected Failure' == 'not found'
    except:
        if fail:
            return
        if alternative:
            run_python_package_import_test(test_case, alternative,fail)
        else:
            raise
