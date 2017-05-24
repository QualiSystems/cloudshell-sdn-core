import jsonpickle

from cloudshell.core.action_result import ActionResult
from cloudshell.core.driver_response import DriverResponse
from cloudshell.core.driver_response_root import DriverResponseRoot
from cloudshell.networking.sdn.static_flows.static_flows_configuration import InstallStaticFlows


class JsonRequestDeserializer(object):
    def __init__(self, json):
        for key, value in json.items():
            if isinstance(value, dict):
                setattr(self, key, JsonRequestDeserializer(value))
            elif isinstance(value, list):
                items = [self._create_obj_by_type(item) for item in value]
                setattr(self, key, items)
            else:
                setattr(self, key, self._create_obj_by_type(value))

    @staticmethod
    def _create_obj_by_type(obj):
        obj_type = type(obj)
        if obj_type == dict:
            return JsonRequestDeserializer(obj)
        if obj_type == list:
            return [JsonRequestDeserializer._create_obj_by_type(item) for item in obj]
        if JsonRequestDeserializer._is_primitive(obj):
            return obj_type(obj)
        return obj

    @staticmethod
    def _is_primitive(thing):
        primitive = (int, str, bool, float, unicode)
        return isinstance(thing, primitive)


class ApplyConnectivityOperation(InstallStaticFlows):

    def _serialize_to_json(self, result, unpicklable=False):
        """Serializes output as JSON and writes it to console output wrapped with special prefix and suffix
        :param result: Result to return
        :param unpicklable: If True adds JSON can be deserialized as real object.
                            When False will be deserialized as dictionary
        """

        json = jsonpickle.encode(result, unpicklable=unpicklable)
        result_for_output = str(json)
        return result_for_output

    def _prepare_action_result(self, action):
        action_result = ActionResult()
        action_result.type = action.type
        action_result.actionId = action.actionId
        action_result.errorMessage = None
        action_result.infoMessage = None
        action_result.updatedInterface = action.actionTarget.fullName

        return action_result

    def apply_connectivity_changes(self, request):
        self.logger.info("Apply connectivity request:\n {}".format(request))

        if request is None or request == "":
            raise Exception(self.__class__.__name__, "request is None or empty")

        holder = JsonRequestDeserializer(jsonpickle.decode(request))

        if not holder or not hasattr(holder, "driverRequest"):
            raise Exception(self.__class__.__name__, "Deserialized request is None or empty")

        driver_response = DriverResponse()
        driver_response_root = DriverResponseRoot()
        connects = {}
        disconnects = {}
        request_result = []

        for action in holder.driverRequest.actions:
            vlan_id = action.connectionParams.vlanId

            if action.type == "setVlan":
                connects.setdefault(vlan_id, []).append(action)

            elif action.type == "removeVlan":
                disconnects.setdefault(vlan_id, []).append(action)

        for actions in connects.itervalues():
            if len(actions) != 2:
                action = actions[0]
                action_result = self._prepare_action_result(action)
                action_result.errorMessage = "Can't find another switch to connect to"
                request_result.append(action_result)
                continue

            for action in actions:
                action_result = self._prepare_action_result(action)

                full_addr = action.actionTarget.fullAddress
                full_name = action.actionTarget.fullName
                full_addr_parts = full_addr.split("/")
                src_port = full_addr_parts[-1]
                switch_id = full_addr_parts[-2]
                port_name = full_name.split("/")[-1]

                try:
                    self.static_flow_pusher(port_name, switch_id, src_port)

                except Exception:
                    action_result.errorMessage = "Failed to connect {}".format(full_name)

                else:
                    action_result.infoMessage = "Successfully connected {}".format(full_name)

                request_result.append(action_result)

            self.remove_static_files_folder()

        for actions in disconnects.itervalues():
            if len(actions) != 2:
                action = actions[0]
                action_result = self._prepare_action_result(action)
                action_result.errorMessage = "Can't find another switch to disconnect from"
                request_result.append(action_result)
                continue

            for action in actions:
                action_result = self._prepare_action_result(action)

                full_addr = action.actionTarget.fullAddress
                full_name = action.actionTarget.fullName
                full_addr_parts = full_addr.split("/")
                src_port = full_addr_parts[-1]
                switch_id = full_addr_parts[-2]
                port_name = full_name.split("/")[-1]

                try:
                    self.delete_static_flow(flow_name=port_name, switch_id=switch_id, port=src_port)

                except Exception:
                    action_result.errorMessage = "Failed to disconnect {}".format(full_name)

                else:
                    action_result.infoMessage = "Successfully disconnected {}".format(full_name)

                request_result.append(action_result)

        driver_response.actionResults = request_result
        driver_response_root.driverResponse = driver_response

        return self._serialize_to_json(driver_response_root).replace("[true]", "true")
