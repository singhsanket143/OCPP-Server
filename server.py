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
    
    @on(Action.DataTransfer)
    def on_data_transfer(self, vendor_id, message_id, data):
        return call_result.DataTransferPayload(
            vendorId=vendor_id,
            messageId=message_id,
            data=data
        )
    
    @on(Action.Heartbeat)
    def heart_beat(self):
        return call_result.HeartbeatPayload()

    @on(Action.MeterValues)
    def meter_values(self, connector_id, meter_value, transaction_id):
        return call_result.MeterValuesPayload(
            connectorId=connector_id,
            meterValue=meter_value,
            transactionId=transaction_id
        )

    @on(Action.StartTransaction)
    def on_start_transaction(self, connector_id, id_tag, meter_start, time_stamp, reservaltion_id):
        return call_result.StartTransactionPayload(
            connectorId=connector_id,
            idTag=id_tag,
            meterStart=meter_start,
            timeStamp=time_stamp,
            reservationId=reservaltion_id
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
