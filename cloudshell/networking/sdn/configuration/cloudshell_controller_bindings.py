import cloudshell.networking.sdn.configuration.cloudshell_controller_configuration as config
import inject


def bindings(binder):
    """
    Binding for controller handler
    :param binder: The Binder object for binding creation
    :type binder: inject.Binder
    """

    try:
        binder.bind_to_provider('controller_handler', config.CONTROLLER_HANDLER)
    except inject.InjectorException:
        pass

    try:
        binder.bind_to_provider('topology_handler', config.TOPOLOGY_HANDLER)
    except inject.InjectorException:
        pass
