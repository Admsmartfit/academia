import sys
from flask.cli import main
try:
    sys.argv = ['flask', 'db', 'upgrade']
    main()
except Exception as e:
    import traceback
    with open('error_detailed.txt', 'w', encoding='utf-8') as f:
        traceback.print_exc(file=f)
    print(f"Error caught: {e}")
