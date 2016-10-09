import web
import sys
import os
import json


PACKAGE_DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEBAPP_DIR_PATH = os.path.normpath(os.path.join(PACKAGE_DIR_PATH, 'webapp'))
UTIL_DIR_PATH = os.path.normpath(os.path.join(PACKAGE_DIR_PATH, 'util'))

if WEBAPP_DIR_PATH not in sys.path:
    sys.path.insert(0, WEBAPP_DIR_PATH)

if UTIL_DIR_PATH not in sys.path:
    sys.path.insert(0, UTIL_DIR_PATH)

from mongoDB.mongodb import MongoDB as MongoDB

PERSON_COLL_NAME = 'Person'
EVENT_COLL_NAME = 'Event'
FRIENDS_COLL_NAME = 'Friends'

MONGODB_INSTANCE = MongoDB()
        
urls = (
    '/api/setupUser/$', 'SetUpUser',
    '/api/registerEvent/$', 'RegisterEventForUser',
    '/api/activateEvent/$', 'ActivateEventForUser',
    '/api/closeEvent/$', 'CloseEventForUser',
    '/api/getEventList/$', 'GetEventsListForUser',
    '/api/addConnection/$', 'AddConnection',
    '/api/getFriendsDetails/$', 'GetEventFriendsAndProfilesForUser'
)

app = web.application(urls, globals())

class SetUpUser:

    def POST(self):

        request_data = web.input()

        dbData = {
            'name': request_data['name'],
            'emailId': request_data['emailId'],
            'contact_info': {
                'address': request_data.get('address', None),
                'phone': request_data.get('phone', None)
            },
            'social': {
                'facebook': request_data.get('facebook', None),
                'linkedin': request_data.get('linkedin', None),
                'twitter': request_data.get('twitter', None),
                'github': request_data.get('github', None),
                'topcoder': request_data.get('topcoder', None)
            }
        }

        MONGODB_INSTANCE.insert_document_in_collection(
            PERSON_COLL_NAME,
            dbData,
            'name'
        )

class RegisterEventForUser:

    def POST(self):

        requestData = web.input()

        dbData = {
          "eventName" : requestData['eventName'],
          "emailId" : requestData['emailId'],
          "sharedProfiles": requestData['sharedProfiles'],
          "isActive": False
        }

        MONGODB_INSTANCE.insert_document_in_collection(
            EVENT_COLL_NAME,
            dbData,
            ["eventName", "emailId"]
        )


class ActivateEventForUser:

    def POST(self):

        requestData = web.input()

        spec = {"emailId" : requestData['emailId']}

        update_doc = {

            "$set":
                {
                    "isActive": False
                }
        }

        MONGODB_INSTANCE.update_collection(
                EVENT_COLL_NAME,
                spec,
                update_doc,
                upsert = False,
                update_one=False
        )


        spec = {"eventName": requestData['eventName'], "emailId" : requestData['emailId']}

        update_doc = {

            "$set":
                {
                    "isActive": True
                }
        }

        MONGODB_INSTANCE.update_collection(
                EVENT_COLL_NAME,
                spec,
                update_doc,
                upsert = False,
                update_one=True
        )



class CloseEventForUser:

    def POST(self):

        requestData = web.input()
        
        spec = {"eventName": requestData['eventName'], "emailId" : requestData['emailId']}

        update_doc = {

            "$set":
                {
                    "isActive": False
                }
        }

        MONGODB_INSTANCE.update_collection(
                EVENT_COLL_NAME,
                spec,
                update_doc,
                upsert = False,
                update_one=True
        )


class GetEventsListForUser:

    def POST(self):

        requestData = web.input()
        # print requestData.get('emailId', 0), type(requestData)
        # requestData = json.loads(requestData)
        # print requestData
        # import pprint
        # pprint.pprint(requestData)

        query = {
            'emailId': requestData['emailId']
        }

        eventRecordsCursor = MONGODB_INSTANCE.find(collection=EVENT_COLL_NAME, query=query)
        eventNamesList = {"eventNames":[], "isError":False, "errorMessage":"No Error"}

        web.header("Content-Type", "application/json")

        if eventRecordsCursor.count() <= 0:
            eventNamesList["isError"] = True
            eventNamesList["errorMessage"] = "No Event found for you!"
            return json.dumps(eventNamesList)



        for eventRecord in eventRecordsCursor:
            eventNamesList["eventNames"].append(eventRecord["eventName"])

        return json.dumps(eventNamesList)


class AddConnection:

    def POST(self):

        requestData = web.input()

        
        # Get master user's active event
        query = {
            "emailId" : requestData["emailId"],
            "isActive" : True
        }

        eventRecordCursor = MONGODB_INSTANCE.find(collection=EVENT_COLL_NAME, query=query, one_record=True)

        if not eventRecordCursor:
          print "No Active event found for master user with email Id: ", requestData['emailId']
          return

        masterUserActiveEventName = eventRecordCursor["eventName"]
        
        # Get connected user's connected event
        query = {
            'emailId': requestData['friendEmailId'],
            "isActive" : True
        }

        eventRecordCursor = MONGODB_INSTANCE.find(collection=EVENT_COLL_NAME, query=query, one_record=True)

        if not eventRecordCursor:
          print "No Active event found for connected member with email Id: ", requestData['friendEmailId']
          return

        connectedMemberActiveEventName = eventRecordCursor["eventName"]


        dbData = {
            "emailId" : requestData["emailId"],
            "eventName" : requestData["eventName"],
            "friendEmailId" : requestData["friendEmailId"],
            "friendEventName" : connectedMemberActiveEventName

        }

        MONGODB_INSTANCE.insert_document_in_collection(
            FRIENDS_COLL_NAME,
            dbData,
            ["emailId", "eventName","friendEmailId", "friendEventName"]
        )

class GetEventFriendsAndProfilesForUser:

    def POST(self):

        requestData = web.input()

        print requestData

        web.header("Content-Type","application/json")

        query = {
            'eventName': requestData['eventName'],
            'emailId': requestData['emailId']
        }

        friendsCursorRecord = MONGODB_INSTANCE.find(
                                collection=FRIENDS_COLL_NAME, 
                                query=query

                              )
        friendsMadeAtEvent = list(friendsCursorRecord)
        
        outputData = {}

        if len(friendsMadeAtEvent) <= 0:
            print "No friend made at the event"
            return json.dumps(outputData)

        friendsEmailAndEvent = []

        for doc in friendsMadeAtEvent:
            friendEmailAndEvent = {}
            friendEmailAndEvent["emailId"] = doc["friendEmailId"]
            friendEmailAndEvent["eventName"] = doc["friendEventName"]
            friendsEmailAndEvent.append(friendEmailAndEvent)

        friendListEventDetails = MONGODB_INSTANCE.findRecordsForDicts(
                                EVENT_COLL_NAME,
                                friendsEmailAndEvent
                            )
        if friendListEventDetails.count() <= 0:

            return json.dumps({"sss":"dd"})

        friendsEventDetails = list(friendListEventDetails)
        friendsEmaildIdToSharedProfile = {}

        for doc in friendsEventDetails:
            friendsEmaildIdToSharedProfile[doc["emailId"]] = doc["sharedProfiles"]

        query = {
            'emailId': {"$in": friendsEmaildIdToSharedProfile.keys()}
        }

        friendDetailsCursor = list(MONGODB_INSTANCE.find(
                                collection=PERSON_COLL_NAME, 
                                query=query
                              ))

        outputData = []

        for doc in friendDetailsCursor:
            friendEmailId = doc["emailId"]
            friendSocialProfiles = doc["social"]
            friendname = doc["name"]

            sharedProfiles = friendsEmaildIdToSharedProfile[friendEmailId]
            sharedProfilesList = map(lambda x: x.strip(), sharedProfiles.split(","))

            friendData = {}
            friendData["social"] = {}
            friendData["name"] = friendname

            for profileName in sharedProfilesList:
                if profileName in friendSocialProfiles:
                    profile_details = friendSocialProfiles[profileName]
                    friendData["social"][profileName] = profile_details

            outputData.append(friendData)

        return json.dumps(
            {
            "eventFriendsList": outputData
        })

    @staticmethod
    def __parse_message_for_maf(data):
        result = {}
        social_websites = ['facebook', 'twitter', 'linkedin']

        for datum in data:

            result[datum['name']] = [
                'Facebook:' + datum['social'].get('facebook', ''),
                'Twitter:' + datum['social'].get('twitter', ''),
                'LinkedIn: ' + datum['social'].get('linkedin', '')
            ]

        return result


if __name__ == "__main__":
    app.run()