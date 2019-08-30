import asyncio
import websockets
from pymongo import MongoClient
from datetime import datetime

from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import Action, RegistrationStatus
from ocpp.v16 import call_result

client = MongoClient('localhost', 27017)
mydatabase = client['ocppdb'] 

class ChargePoint(cp):
    @on(Action.Authorize)
    def authorize(self, id_tag):
        record_count = 0
        result = mydatabase.vehicle.find({"idTag": id_tag})
        result_iter = {}
        response = {"title": "AuthorizeResponse", "type": "object"}
        for x in result:
            record_count += 1
            result_iter = x
        if(record_count != 0):
            response["properties"] = {}
            response["properties"]["idTagInfo"] = {"status": result_iter["status"], "expiryDate": result_iter["expiryDate"], "parentIdTag": result_iter["parentIdTag"]}
        else:
            response["properties"] = {}
            response["properties"]["idTagInfo"] = {"status": "Invalid"}
        
        return response

    @on(Action.BootNotification)
    def on_boot_notitication(self, charge_point_vendor, charge_point_model, **kwargs):
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=10,
            status=RegistrationStatus.accepted
        )

    @on(Action.ChangeAvailability)
    def on_change_availability(self, connector_id, type):
        return call_result.ChangeAvailabilityPayload(
            status=RegistrationStatus.accepted
        )
    
    @on(Action.ChangeConfiguration)
    def on_change_configuration(self, key, value):
        return call_result.ChangeConfigurationPayload(
            status=RegistrationStatus.accepted
        )

    @on(Action.ClearCache)
    def on_clear_cache():
        return call_result.ClearCachePayload(
            status=RegistrationStatus.accepted
        )
    
    
async def on_connect(websocket, path):
    """ For every new charge point that connects, create a ChargePoint instance
    and start listening for messages.

    """
    charge_point_id = path.strip('/')
    cp = ChargePoint(charge_point_id, websocket)
    print("On Connect On The Server Hit")
    await cp.start()


async def main():
    server = await websockets.serve(
        on_connect,
        '0.0.0.0',
        9000,
        subprotocols=['ocpp1.6']
    )

    await server.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())
