/* automatically generated by genlutable.sh, do not edit directly */
#ifndef LOGTAG_NAMES_DEFINED
#define LOGTAG_NAMES_DEFINED


enum
{

  LOGTAG_CORE_ACCOUNTING=1,
  LOGTAG_CORE_AUTH=2,
  LOGTAG_CORE_DEBUG=3,
  LOGTAG_CORE_DUMP=4,
  LOGTAG_CORE_ERROR=5,
  LOGTAG_CORE_INFO=6,
  LOGTAG_CORE_LICENSE=7,
  LOGTAG_CORE_MESSAGE=8,
  LOGTAG_CORE_POLICY=9,
  LOGTAG_CORE_SESSION=10,
  LOGTAG_CORE_STDERR=11,
  LOGTAG_FINGER_DEBUG=12,
  LOGTAG_FINGER_ERROR=13,
  LOGTAG_FINGER_POLICY=14,
  LOGTAG_FINGER_REQUEST=15,
  LOGTAG_FINGER_VIOLATION=16,
  LOGTAG_FTP_DEBUG=17,
  LOGTAG_FTP_ERROR=18,
  LOGTAG_FTP_POLICY=19,
  LOGTAG_FTP_REPLY=20,
  LOGTAG_FTP_REQUEST=21,
  LOGTAG_FTP_SESSION=22,
  LOGTAG_FTP_VIOLATION=23,
  LOGTAG_HTTP_ACCOUNTING=24,
  LOGTAG_HTTP_DEBUG=25,
  LOGTAG_HTTP_INFO=26,
  LOGTAG_HTTP_ERROR=27,
  LOGTAG_HTTP_POLICY=28,
  LOGTAG_HTTP_REQUEST=29,
  LOGTAG_HTTP_RESPONSE=30,
  LOGTAG_HTTP_VIOLATION=31,
  LOGTAG_IMAP_DEBUG=32,
  LOGTAG_IMAP_ERROR=33,
  LOGTAG_IMAP_INFO=34,
  LOGTAG_IMAP_POLICY=35,
  LOGTAG_IMAP_REPLY=36,
  LOGTAG_IMAP_REQUEST=37,
  LOGTAG_IMAP_VIOLATION=38,
  LOGTAG_LDAP_DEBUG=39,
  LOGTAG_LDAP_ERROR=40,
  LOGTAG_LDAP_POLICY=41,
  LOGTAG_LDAP_REQUEST=42,
  LOGTAG_LDAP_RESPONSE=43,
  LOGTAG_LDAP_VIOLATION=44,
  LOGTAG_LP_DEBUG=45,
  LOGTAG_LP_ERROR=46,
  LOGTAG_LP_POLICY=47,
  LOGTAG_LP_REQUEST=48,
  LOGTAG_MIME_ERROR=49,
  LOGTAG_MIME_POLICY=50,
  LOGTAG_MIME_VIOLATION=51,
  LOGTAG_MSRPC_DEBUG=52,
  LOGTAG_MSRPC_ERROR=53,
  LOGTAG_MSRPC_INFO=54,
  LOGTAG_MSRPC_POLICY=55,
  LOGTAG_MSRPC_SESSION=56,
  LOGTAG_MSRPC_VIOLATION=57,
  LOGTAG_NNTP_DEBUG=58,
  LOGTAG_NNTP_POLICY=59,
  LOGTAG_NNTP_REPLY=60,
  LOGTAG_NNTP_REQUEST=61,
  LOGTAG_NNTP_TRACE=62,
  LOGTAG_PLUG_DEBUG=63,
  LOGTAG_PLUG_ERROR=64,
  LOGTAG_PLUG_POLICY=65,
  LOGTAG_PLUG_SESSION=66,
  LOGTAG_POP3_DEBUG=67,
  LOGTAG_POP3_ERROR=68,
  LOGTAG_POP3_POLICY=69,
  LOGTAG_POP3_REPLY=70,
  LOGTAG_POP3_REQUEST=71,
  LOGTAG_POP3_VIOLATION=72,
  LOGTAG_PSSL_DEBUG=73,
  LOGTAG_PSSL_ERROR=74,
  LOGTAG_PSSL_POLICY=75,
  LOGTAG_RADIUS_DEBUG=76,
  LOGTAG_RADIUS_ERROR=77,
  LOGTAG_RADIUS_POLICY=78,
  LOGTAG_RADIUS_REQUEST=79,
  LOGTAG_RADIUS_SESSION=80,
  LOGTAG_RADIUS_VIOLATION=81,
  LOGTAG_RDP_DEBUG=82,
  LOGTAG_RDP_ERROR=83,
  LOGTAG_RDP_INFO=84,
  LOGTAG_RDP_POLICY=85,
  LOGTAG_RDP_SESSION=86,
  LOGTAG_RDP_VIOLATION=87,
  LOGTAG_RSH_ACCOUNTING=88,
  LOGTAG_RSH_DEBUG=89,
  LOGTAG_RSH_ERROR=90,
  LOGTAG_RSH_POLICY=91,
  LOGTAG_RSH_VIOLATION=92,
  LOGTAG_SATYR_ERROR=93,
  LOGTAG_SIP_VIOLATION=94,
  LOGTAG_SIP_REQUEST=95,
  LOGTAG_SIP_RESPONSE=96,
  LOGTAG_SIP_POLICY=97,
  LOGTAG_SIP_DEBUG=98,
  LOGTAG_SIP_ERROR=99,
  LOGTAG_SIP_ACCOUNTING=100,
  LOGTAG_SMTP_ACCOUNTING=101,
  LOGTAG_SMTP_DEBUG=102,
  LOGTAG_SMTP_ERROR=103,
  LOGTAG_SMTP_INFO=104,
  LOGTAG_SMTP_POLICY=105,
  LOGTAG_SMTP_REQUEST=106,
  LOGTAG_SMTP_RESPONSE=107,
  LOGTAG_SMTP_VIOLATION=108,
  LOGTAG_SQLNET_ERROR=109,
  LOGTAG_SQLNET_REQUEST=110,
  LOGTAG_SQLNET_VIOLATION=111,
  LOGTAG_SSH_DEBUG=112,
  LOGTAG_SSH_ERROR=113,
  LOGTAG_SSH_POLICY=114,
  LOGTAG_SSH_VIOLATION=115,
  LOGTAG_SSH_ACCOUNTING=116,
  LOGTAG_SSH_INFO=117,
  LOGTAG_TELNET_DEBUG=118,
  LOGTAG_TELNET_ERROR=119,
  LOGTAG_TELNET_POLICY=120,
  LOGTAG_TELNET_VIOLATION=121,
  LOGTAG_TELNET_VIOLATIONS=122,
  LOGTAG_TFTP_DEBUG=123,
  LOGTAG_TFTP_ERROR=124,
  LOGTAG_TFTP_POLICY=125,
  LOGTAG_TFTP_REQUEST=126,
  LOGTAG_TFTP_VIOLATION=127,
  LOGTAG_TLS_ACCOUNTING=128,
  LOGTAG_VNC_DEBUG=129,
  LOGTAG_VNC_ERROR=130,
  LOGTAG_VNC_INFO=131,
  LOGTAG_VNC_POLICY=132,
  LOGTAG_VNC_SESSION=133,
  LOGTAG_VNC_VIOLATION=134,
  LOGTAG_WHOIS_DEBUG=135,
  LOGTAG_WHOIS_ERROR=136,
  LOGTAG_WHOIS_REQUEST=137,
  LOGTAG_X11_DEBUG=138,
  LOGTAG_X11_ERROR=139,
  LOGTAG_X11_INFO=140,
  LOGTAG_X11_POLICY=141,
  LOGTAG_X11_SESSION=142,
  LOGTAG_X11_VIOLATION=143,
  LOGTAG_MAX=144

};

#endif


