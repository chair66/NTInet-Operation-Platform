from app.config import get_settings
from app.services.bandwidth import BandwidthSDK

settings = get_settings()
bw = BandwidthSDK(settings)
