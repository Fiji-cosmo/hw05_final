from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    dt_year_now = datetime.now().year
    return {
        'year': dt_year_now,
    }
