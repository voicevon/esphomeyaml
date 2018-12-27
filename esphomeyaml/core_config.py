import logging
import os
import re

import voluptuous as vol

from esphomeyaml import automation, pins
import esphomeyaml.config_validation as cv
from esphomeyaml.const import ARDUINO_VERSION_ESP32_DEV, ARDUINO_VERSION_ESP8266_DEV, \
    CONF_ARDUINO_VERSION, CONF_BOARD, CONF_BOARD_FLASH_MODE, CONF_BRANCH, CONF_BUILD_PATH, \
    CONF_COMMIT, CONF_ESPHOMELIB_VERSION, CONF_ESPHOMEYAML, CONF_LOCAL, CONF_NAME, CONF_ON_BOOT, \
    CONF_ON_LOOP, CONF_ON_SHUTDOWN, CONF_PLATFORM, CONF_PRIORITY, CONF_REPOSITORY, CONF_TAG, \
    CONF_TRIGGER_ID, CONF_USE_CUSTOM_CODE, ESPHOMELIB_VERSION, ESP_PLATFORM_ESP32, \
    ESP_PLATFORM_ESP8266, CONF_LIBRARIES, CONF_INCLUDES
from esphomeyaml.core import CORE, EsphomeyamlError
from esphomeyaml.cpp_generator import Pvariable, RawExpression, add
from esphomeyaml.cpp_types import App, NoArg, const_char_ptr, esphomelib_ns
from esphomeyaml.py_compat import text_type

_LOGGER = logging.getLogger(__name__)

LIBRARY_URI_REPO = u'https://github.com/OttoWinter/esphomelib.git'
GITHUB_ARCHIVE_ZIP = u'https://github.com/OttoWinter/esphomelib/archive/{}.zip'

BUILD_FLASH_MODES = ['qio', 'qout', 'dio', 'dout']
StartupTrigger = esphomelib_ns.StartupTrigger
ShutdownTrigger = esphomelib_ns.ShutdownTrigger
LoopTrigger = esphomelib_ns.LoopTrigger

VERSION_REGEX = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+(?:[ab]\d+)?$')


def validate_board(value):
    if CORE.is_esp8266:
        board_pins = pins.ESP8266_BOARD_PINS
    elif CORE.is_esp32:
        board_pins = pins.ESP32_BOARD_PINS
    else:
        raise NotImplementedError

    if value not in board_pins:
        raise vol.Invalid(u"Could not find board '{}'. Valid boards are {}".format(
            value, u', '.join(pins.ESP8266_BOARD_PINS.keys())))
    return value


def validate_simple_esphomelib_version(value):
    value = cv.string_strict(value)
    if value.upper() == 'LATEST':
        if ESPHOMELIB_VERSION == 'dev':
            return validate_simple_esphomelib_version('dev')
        return {
            CONF_REPOSITORY: LIBRARY_URI_REPO,
            CONF_TAG: 'v' + ESPHOMELIB_VERSION,
        }
    elif value.upper() == 'DEV':
        return {
            CONF_REPOSITORY: LIBRARY_URI_REPO,
            CONF_BRANCH: 'dev'
        }
    elif VERSION_REGEX.match(value) is not None:
        return {
            CONF_REPOSITORY: LIBRARY_URI_REPO,
            CONF_TAG: 'v' + value,
        }
    raise vol.Invalid("Only simple esphomelib versions!")


def validate_local_esphomelib_version(value):
    value = cv.directory(value)
    path = CORE.relative_path(value)
    library_json = os.path.join(path, 'library.json')
    if not os.path.exists(library_json):
        raise vol.Invalid(u"Could not find '{}' file. '{}' does not seem to point to an "
                          u"esphomelib copy.".format(library_json, value))
    return value


def validate_commit(value):
    value = cv.string(value)
    if re.match(r"^[0-9a-f]{7,}$", value) is None:
        raise vol.Invalid("Commit option only accepts commit hashes in hex format.")
    return value


ESPHOMELIB_VERSION_SCHEMA = vol.Any(
    validate_simple_esphomelib_version,
    vol.Schema({
        vol.Required(CONF_LOCAL): validate_local_esphomelib_version,
    }),
    vol.All(
        vol.Schema({
            vol.Optional(CONF_REPOSITORY, default=LIBRARY_URI_REPO): cv.string,
            vol.Optional(CONF_COMMIT): validate_commit,
            vol.Optional(CONF_BRANCH): cv.string,
            vol.Optional(CONF_TAG): cv.string,
        }),
        cv.has_at_most_one_key(CONF_COMMIT, CONF_BRANCH, CONF_TAG)
    ),
)


def validate_platform(value):
    value = cv.string(value)
    if value.upper() in ('ESP8266', 'ESPRESSIF8266'):
        return ESP_PLATFORM_ESP8266
    if value.upper() in ('ESP32', 'ESPRESSIF32'):
        return ESP_PLATFORM_ESP32
    raise vol.Invalid(u"Invalid platform '{}'. Only options are ESP8266 and ESP32. Please note "
                      u"the old way to use the latest arduino framework version has been split up "
                      u"into the arduino_version configuration option.".format(value))


PLATFORMIO_ESP8266_LUT = {
    '2.4.2': 'espressif8266@1.8.0',
    '2.4.1': 'espressif8266@1.7.3',
    '2.4.0': 'espressif8266@1.6.0',
    '2.3.0': 'espressif8266@1.5.0',
    'RECOMMENDED': 'espressif8266@1.8.0',
    'LATEST': 'espressif8266',
    'DEV': ARDUINO_VERSION_ESP8266_DEV,
}

PLATFORMIO_ESP32_LUT = {
    '1.0.0': 'espressif32@1.4.0',
    'RECOMMENDED': 'espressif32@1.5.0',
    'LATEST': 'espressif32',
    'DEV': ARDUINO_VERSION_ESP32_DEV,
}


def validate_arduino_version(value):
    value = cv.string_strict(value)
    value_ = value.upper()
    if CORE.is_esp8266:
        if VERSION_REGEX.match(value) is not None and value_ not in PLATFORMIO_ESP8266_LUT:
            raise vol.Invalid("Unfortunately the arduino framework version '{}' is unsupported "
                              "at this time. You can override this by manually using "
                              "espressif8266@<platformio version>")
        if value_ in PLATFORMIO_ESP8266_LUT:
            return PLATFORMIO_ESP8266_LUT[value_]
        return value
    elif CORE.is_esp32:
        if VERSION_REGEX.match(value) is not None and value_ not in PLATFORMIO_ESP32_LUT:
            raise vol.Invalid("Unfortunately the arduino framework version '{}' is unsupported "
                              "at this time. You can override this by manually using "
                              "espressif32@<platformio version>")
        if value_ in PLATFORMIO_ESP32_LUT:
            return PLATFORMIO_ESP32_LUT[value_]
        return value
    raise NotImplementedError


def default_build_path():
    return CORE.name


CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.valid_name,
    vol.Required(CONF_PLATFORM): cv.one_of('ESP8266', 'ESPRESSIF8266', 'ESP32', 'ESPRESSIF32',
                                           upper=True),
    vol.Required(CONF_BOARD): validate_board,
    vol.Optional(CONF_ESPHOMELIB_VERSION, default='latest'): ESPHOMELIB_VERSION_SCHEMA,
    vol.Optional(CONF_ARDUINO_VERSION, default='recommended'): validate_arduino_version,
    vol.Optional(CONF_USE_CUSTOM_CODE, default=False): cv.boolean,
    vol.Optional(CONF_BUILD_PATH, default=default_build_path): cv.string,

    vol.Optional(CONF_BOARD_FLASH_MODE): cv.one_of(*BUILD_FLASH_MODES, lower=True),
    vol.Optional(CONF_ON_BOOT): automation.validate_automation({
        cv.GenerateID(CONF_TRIGGER_ID): cv.declare_variable_id(StartupTrigger),
        vol.Optional(CONF_PRIORITY): cv.float_,
    }),
    vol.Optional(CONF_ON_SHUTDOWN): automation.validate_automation({
        cv.GenerateID(CONF_TRIGGER_ID): cv.declare_variable_id(ShutdownTrigger),
    }),
    vol.Optional(CONF_ON_LOOP): automation.validate_automation({
        cv.GenerateID(CONF_TRIGGER_ID): cv.declare_variable_id(LoopTrigger),
    }),
    vol.Optional(CONF_INCLUDES): cv.ensure_list(cv.file_),
    vol.Optional(CONF_LIBRARIES): cv.ensure_list(cv.string_strict),

    vol.Optional('library_uri'): cv.invalid("The library_uri option has been removed in 1.8.0 and "
                                            "was moved into the esphomelib_version option."),
    vol.Optional('use_build_flags'): cv.invalid("The use_build_flags option has been replaced by "
                                                "use_custom_code option in 1.8.0."),
})


def preload_core_config(config):
    if CONF_ESPHOMEYAML not in config:
        raise EsphomeyamlError(u"No esphomeyaml section in config")
    core_conf = config[CONF_ESPHOMEYAML]
    if CONF_PLATFORM not in core_conf:
        raise EsphomeyamlError("esphomeyaml.platform not specified.")
    if CONF_BOARD not in core_conf:
        raise EsphomeyamlError("esphomeyaml.board not specified.")
    if CONF_NAME not in core_conf:
        raise EsphomeyamlError("esphomeyaml.name not specified.")

    try:
        CORE.esp_platform = validate_platform(core_conf[CONF_PLATFORM])
        CORE.board = validate_board(core_conf[CONF_BOARD])
        CORE.name = cv.valid_name(core_conf[CONF_NAME])
        CORE.build_path = CORE.relative_path(
            cv.string(core_conf.get(CONF_BUILD_PATH, default_build_path())))
    except vol.Invalid as e:
        raise EsphomeyamlError(text_type(e))


def to_code(config):
    add(App.set_name(config[CONF_NAME]))

    for conf in config.get(CONF_ON_BOOT, []):
        rhs = App.register_component(StartupTrigger.new(conf.get(CONF_PRIORITY)))
        trigger = Pvariable(conf[CONF_TRIGGER_ID], rhs)
        automation.build_automation(trigger, NoArg, conf)

    for conf in config.get(CONF_ON_SHUTDOWN, []):
        trigger = Pvariable(conf[CONF_TRIGGER_ID], ShutdownTrigger.new())
        automation.build_automation(trigger, const_char_ptr, conf)

    for conf in config.get(CONF_ON_LOOP, []):
        rhs = App.register_component(LoopTrigger.new())
        trigger = Pvariable(conf[CONF_TRIGGER_ID], rhs)
        automation.build_automation(trigger, NoArg, conf)

    add(App.set_compilation_datetime(RawExpression('__DATE__ ", " __TIME__')))


def lib_deps(config):
    return set(config.get(CONF_LIBRARIES, []))


def includes(config):
    ret = []
    for include in config.get(CONF_INCLUDES, []):
        path = CORE.relative_path(include)
        res = os.path.relpath(path, CORE.relative_build_path('src', 'main.cpp'))
        ret.append(u'#include "{}"'.format(res))
    return ret
