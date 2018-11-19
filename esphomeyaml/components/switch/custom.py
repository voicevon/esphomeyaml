import voluptuous as vol

from esphomeyaml.components import binary_sensor, switch
import esphomeyaml.config_validation as cv
from esphomeyaml.const import CONF_BINARY_SENSORS, CONF_ID, CONF_LAMBDA, CONF_SWITCHES
from esphomeyaml.cpp_generator import process_lambda, variable
from esphomeyaml.cpp_types import std_vector

CustomSwitchConstructor = switch.switch_ns.class_('CustomSwitchConstructor')

PLATFORM_SCHEMA = binary_sensor.PLATFORM_SCHEMA.extend({
    cv.GenerateID(): cv.declare_variable_id(CustomSwitchConstructor),
    vol.Required(CONF_LAMBDA): cv.lambda_,
    vol.Required(CONF_SWITCHES):
        vol.All(cv.ensure_list, [switch.SWITCH_SCHEMA.extend({
            cv.GenerateID(): cv.declare_variable_id(switch.Switch),
        })]),
})


def to_code(config):
    for template_ in process_lambda(config[CONF_LAMBDA], [],
                                    return_type=std_vector.template(switch.SwitchPtr)):
        yield

    rhs = CustomSwitchConstructor(template_)
    custom = variable(config[CONF_ID], rhs)
    for i, sens in enumerate(config[CONF_SWITCHES]):
        switch.register_switch(custom.get_switch(i), sens)


BUILD_FLAGS = '-DUSE_CUSTOM_BINARY_SENSOR'


def to_hass_config(data, config):
    return [binary_sensor.core_to_hass_config(data, sens) for sens in config[CONF_BINARY_SENSORS]]
