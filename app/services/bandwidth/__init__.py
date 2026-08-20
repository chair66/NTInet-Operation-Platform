from app.config import Settings
from .client import BandwidthClient
from .csr import CSRService
from .errors import BandwidthAPIError
from .error_translator import translate_bandwidth_error
from .inventory import InventoryService
from .porting import PortingService
from .ordering import OrderingService
from .line_features import LineFeaturesService
from .messaging import MessagingService


class BandwidthSDK:
    def __init__(self, settings: Settings):
        self.client = BandwidthClient(settings)
        self.inventory = InventoryService(self.client)
        self.porting = PortingService(self.client)
        self.ordering = OrderingService(self.client)
        self.csr = CSRService(self.client)
        self.line_features = LineFeaturesService(self.client)
        self.messaging = MessagingService(self.client)
