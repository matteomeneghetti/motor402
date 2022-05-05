SW_MASK = {
    'NOT READY TO SWITCH ON':       (0x4F, 0x00),
    'SWITCH ON DISABLED':           (0x4F, 0x40),
    'READY TO SWITCH ON':           (0x6F, 0x21),
    'SWITCHED ON':                  (0x6F, 0x23),
    'OPERATION ENABLED':            (0x6F, 0x27),
    'FAULT':                        (0x4F, 0x08),
    'FAULT REACTION ACTIVE':        (0x4F, 0x0F),
    'QUICK STOP ACTIVE':            (0x6F, 0x07)
}

# Controlword (0x6040) commands
CW_OPERATION_ENABLED = 0x000F
CW_SHUTDOWN = 0x0006
CW_SWITCH_ON = 0x0007
CW_QUICK_STOP = 0x0002
CW_DISABLE_VOLTAGE = 0x0000
CW_SWITCH_ON_DISABLED = 0x0080

TRANSITIONTABLE = {
    # disable_voltage ---------------------------------------------------------------------
    ('READY TO SWITCH ON', 'SWITCH ON DISABLED'):     CW_DISABLE_VOLTAGE,  # transition 7
    ('OPERATION ENABLED', 'SWITCH ON DISABLED'):      CW_DISABLE_VOLTAGE,  # transition 9
    ('SWITCHED ON', 'SWITCH ON DISABLED'):            CW_DISABLE_VOLTAGE,  # transition 10
    ('QUICK STOP ACTIVE', 'SWITCH ON DISABLED'):      CW_DISABLE_VOLTAGE,  # transition 12
    # automatic ---------------------------------------------------------------------------
    ('NOT READY TO SWITCH ON', 'SWITCH ON DISABLED'): 0x00,  # transition 1
    ('START', 'NOT READY TO SWITCH ON'):              0x00,  # transition 0
    ('FAULT REACTION ACTIVE', 'FAULT'):               0x00,  # transition 14
    # shutdown ----------------------------------------------------------------------------
    ('SWITCH ON DISABLED', 'READY TO SWITCH ON'):     CW_SHUTDOWN,  # transition 2
    ('SWITCHED ON', 'READY TO SWITCH ON'):            CW_SHUTDOWN,  # transition 6
    ('OPERATION ENABLED', 'READY TO SWITCH ON'):      CW_SHUTDOWN,  # transition 8
    # switch_on ---------------------------------------------------------------------------
    ('READY TO SWITCH ON', 'SWITCHED ON'):            CW_SWITCH_ON,  # transition 3
    ('OPERATION ENABLED', 'SWITCHED ON'):             CW_SWITCH_ON,  # transition 5
    # enable_operation --------------------------------------------------------------------
    ('SWITCHED ON', 'OPERATION ENABLED'):             CW_OPERATION_ENABLED,  # transition 4
    ('QUICK STOP ACTIVE', 'OPERATION ENABLED'):       CW_OPERATION_ENABLED,  # transition 16
    # quickstop ---------------------------------------------------------------------------
    ('OPERATION ENABLED', 'QUICK STOP ACTIVE'):       CW_QUICK_STOP,  # transition 11
    # fault -------------------------------------------------------------------------------
    ('FAULT', 'SWITCH ON DISABLED'):                  CW_SWITCH_ON_DISABLED,  # transition 15
}


NEXTSTATE2ANY = {
    ('FAULT', 'NOT READY TO SWITCH ON', 'QUICK STOP ACTIVE'):       'SWITCH ON DISABLED',
    ('SWITCH ON DISABLED'):                                         'READY TO SWITCH ON',
    ('READY TO SWITCH ON'):                                         'SWITCHED ON',
    ('SWITCHED ON'):                                                'OPERATION ENABLED',
    ('FAULT REACTION ACTIVE'):                                      'FAULT',
}

to_operation_enabled_map = {
    'FAULT': ('SWITCH ON DISABLED', 'READY TO SWITCH ON', 'SWITCHED ON', 'OPERATION ENABLED'),
    'SWITCH ON DISABLED': ('READY TO SWITCH ON', 'SWITCHED ON', 'OPERATION ENABLED'),
    'READY TO SWITCH ON': ('SWITCHED ON', 'OPERATION ENABLED'),
    'SWITCHED ON': ('OPERATION ENABLED',),
    'QUICK STOP ACTIVE': ('OPERATION ENABLED',),
    'OPERATION ENABLED': ()
}

to_switch_on_disabled = {
    'FAULT': ('SWITCH ON DISABLED',),
    'SWITCH ON DISABLED': (),
    'READY TO SWITCH ON': ('SWITCH ON DISABLED',),
    'SWITCHED ON': ('READY TO SWITCH ON','SWITCH ON DISABLED'),
    'OPERATION ENABLED': ('SWITCHED ON','READY TO SWITCH ON','SWITCH ON DISABLED'),
    'QUICK STOP ACTIVE': ('OPERATION ENABLED','SWITCHED ON','READY TO SWITCH ON','SWITCH ON DISABLED'),
}
