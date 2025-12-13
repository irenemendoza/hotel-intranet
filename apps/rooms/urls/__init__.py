from .rooms_urls import urlpatterns as rooms_urlpatterns
from .rooms_maintenance_urls import urlpatterns as maintenance_urlpatterns
from .rooms_cleaning_urls import urlpatterns as cleaning_urlpatterns

urlpatterns = rooms_urlpatterns + maintenance_urlpatterns + cleaning_urlpatterns

app_name="rooms"