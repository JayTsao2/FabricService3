feature tacacs+
tacacs-server deadtime 60
tacacs-server host 10.66.164.188 key 7 "qseieii"
tacacs-server host 10.66.164.189 key 7 "qseieii"
tacacs-server host 10.66.164.188 test username healthcheck idle-time 5
tacacs-server host 10.66.164.189 test username healthcheck idle-time 5
aaa group server tacacs+ nwadmin
    server 10.66.164.188
    server 10.66.164.189
    source-interface mgmt0
aaa authentication login default group nwadmin
aaa authorization config-commands default group nwadmin local
aaa authorization commands default group nwadmin local
