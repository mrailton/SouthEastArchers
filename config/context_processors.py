from datetime import datetime


def current_year(request):
    """Inject current year into all templates"""
    return {'current_year': datetime.now().year}
