--
-- PostgreSQL database dump
--

\restrict qUAuy3CWKWfTUiTsfoIG7N6FjzHgspqo2KsYFnWsebcRl7IcNob1GTa79GtcV4a

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alerts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alerts (
    id integer NOT NULL,
    device_type character varying,
    device_name character varying,
    device_ip character varying,
    message character varying,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.alerts OWNER TO postgres;

--
-- Name: alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alerts_id_seq OWNER TO postgres;

--
-- Name: alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.alerts_id_seq OWNED BY public.alerts.id;


--
-- Name: baselines; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.baselines (
    id integer NOT NULL,
    device_id integer,
    metric_type character varying,
    hour_of_day integer,
    day_of_week integer,
    avg_value double precision,
    std_dev double precision,
    sample_count integer,
    last_updated timestamp without time zone
);


ALTER TABLE public.baselines OWNER TO postgres;

--
-- Name: baselines_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.baselines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.baselines_id_seq OWNER TO postgres;

--
-- Name: baselines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.baselines_id_seq OWNED BY public.baselines.id;


--
-- Name: equipments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipments (
    id integer NOT NULL,
    name character varying,
    ip character varying,
    tower_id integer,
    is_panel boolean,
    associated_clients integer,
    parent_id integer,
    is_online boolean,
    last_checked timestamp without time zone,
    last_latency integer,
    maintenance_until timestamp without time zone,
    ssh_user character varying,
    ssh_password character varying,
    ssh_port integer,
    snmp_community character varying,
    snmp_version integer,
    snmp_port integer,
    snmp_interface_index integer,
    is_mikrotik boolean,
    mikrotik_interface character varying,
    api_port integer,
    brand character varying,
    equipment_type character varying,
    signal_dbm integer,
    ccq integer,
    connected_clients integer,
    last_traffic_in double precision,
    last_traffic_out double precision
);


ALTER TABLE public.equipments OWNER TO postgres;

--
-- Name: equipments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.equipments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.equipments_id_seq OWNER TO postgres;

--
-- Name: equipments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.equipments_id_seq OWNED BY public.equipments.id;


--
-- Name: latency_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.latency_history (
    id integer NOT NULL,
    equipment_id integer,
    latency double precision,
    packet_loss double precision,
    "timestamp" double precision
);


ALTER TABLE public.latency_history OWNER TO postgres;

--
-- Name: latency_history_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.latency_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.latency_history_id_seq OWNER TO postgres;

--
-- Name: latency_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.latency_history_id_seq OWNED BY public.latency_history.id;


--
-- Name: monitor_targets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.monitor_targets (
    id integer NOT NULL,
    name character varying,
    target character varying,
    type character varying,
    enabled boolean
);


ALTER TABLE public.monitor_targets OWNER TO postgres;

--
-- Name: monitor_targets_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.monitor_targets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.monitor_targets_id_seq OWNER TO postgres;

--
-- Name: monitor_targets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.monitor_targets_id_seq OWNED BY public.monitor_targets.id;


--
-- Name: network_links; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.network_links (
    id integer NOT NULL,
    source_tower_id integer,
    target_tower_id integer,
    type character varying
);


ALTER TABLE public.network_links OWNER TO postgres;

--
-- Name: network_links_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.network_links_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.network_links_id_seq OWNER TO postgres;

--
-- Name: network_links_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.network_links_id_seq OWNED BY public.network_links.id;


--
-- Name: parameters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parameters (
    key character varying NOT NULL,
    value character varying
);


ALTER TABLE public.parameters OWNER TO postgres;

--
-- Name: ping_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ping_logs (
    id integer NOT NULL,
    device_type character varying,
    device_id integer,
    status boolean,
    latency_ms integer,
    "timestamp" timestamp without time zone
)
WITH (autovacuum_vacuum_scale_factor='0.01', autovacuum_analyze_scale_factor='0.005');


ALTER TABLE public.ping_logs OWNER TO postgres;

--
-- Name: ping_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ping_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ping_logs_id_seq OWNER TO postgres;

--
-- Name: ping_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ping_logs_id_seq OWNED BY public.ping_logs.id;


--
-- Name: ping_stats_hourly; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ping_stats_hourly (
    id integer NOT NULL,
    device_type character varying,
    device_id integer,
    avg_latency_ms double precision,
    pkt_loss_percent double precision,
    availability_percent double precision,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.ping_stats_hourly OWNER TO postgres;

--
-- Name: ping_stats_hourly_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ping_stats_hourly_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ping_stats_hourly_id_seq OWNER TO postgres;

--
-- Name: ping_stats_hourly_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ping_stats_hourly_id_seq OWNED BY public.ping_stats_hourly.id;


--
-- Name: synthetic_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.synthetic_logs (
    id integer NOT NULL,
    target character varying,
    test_type character varying,
    latency_ms integer,
    jitter_ms integer,
    status_code integer,
    success boolean,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.synthetic_logs OWNER TO postgres;

--
-- Name: synthetic_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.synthetic_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.synthetic_logs_id_seq OWNER TO postgres;

--
-- Name: synthetic_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.synthetic_logs_id_seq OWNED BY public.synthetic_logs.id;


--
-- Name: tower_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tower_requests (
    id integer NOT NULL,
    name character varying,
    ip character varying,
    latitude double precision,
    longitude double precision,
    requested_by character varying,
    created_at timestamp without time zone,
    status character varying
);


ALTER TABLE public.tower_requests OWNER TO postgres;

--
-- Name: tower_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tower_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tower_requests_id_seq OWNER TO postgres;

--
-- Name: tower_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tower_requests_id_seq OWNED BY public.tower_requests.id;


--
-- Name: towers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.towers (
    id integer NOT NULL,
    name character varying,
    ip character varying,
    latitude double precision,
    longitude double precision,
    observations text,
    is_online boolean,
    last_checked timestamp without time zone,
    parent_id integer,
    maintenance_until timestamp without time zone
);


ALTER TABLE public.towers OWNER TO postgres;

--
-- Name: towers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.towers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.towers_id_seq OWNER TO postgres;

--
-- Name: towers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.towers_id_seq OWNED BY public.towers.id;


--
-- Name: traffic_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.traffic_logs (
    id integer NOT NULL,
    equipment_id integer,
    in_mbps double precision,
    out_mbps double precision,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.traffic_logs OWNER TO postgres;

--
-- Name: traffic_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.traffic_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.traffic_logs_id_seq OWNER TO postgres;

--
-- Name: traffic_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.traffic_logs_id_seq OWNED BY public.traffic_logs.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying,
    email character varying,
    hashed_password character varying,
    role character varying,
    created_at timestamp without time zone,
    last_latitude double precision,
    last_longitude double precision,
    last_location_update timestamp without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: alerts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alerts ALTER COLUMN id SET DEFAULT nextval('public.alerts_id_seq'::regclass);


--
-- Name: baselines id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.baselines ALTER COLUMN id SET DEFAULT nextval('public.baselines_id_seq'::regclass);


--
-- Name: equipments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipments ALTER COLUMN id SET DEFAULT nextval('public.equipments_id_seq'::regclass);


--
-- Name: latency_history id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.latency_history ALTER COLUMN id SET DEFAULT nextval('public.latency_history_id_seq'::regclass);


--
-- Name: monitor_targets id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monitor_targets ALTER COLUMN id SET DEFAULT nextval('public.monitor_targets_id_seq'::regclass);


--
-- Name: network_links id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.network_links ALTER COLUMN id SET DEFAULT nextval('public.network_links_id_seq'::regclass);


--
-- Name: ping_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ping_logs ALTER COLUMN id SET DEFAULT nextval('public.ping_logs_id_seq'::regclass);


--
-- Name: ping_stats_hourly id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ping_stats_hourly ALTER COLUMN id SET DEFAULT nextval('public.ping_stats_hourly_id_seq'::regclass);


--
-- Name: synthetic_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.synthetic_logs ALTER COLUMN id SET DEFAULT nextval('public.synthetic_logs_id_seq'::regclass);


--
-- Name: tower_requests id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tower_requests ALTER COLUMN id SET DEFAULT nextval('public.tower_requests_id_seq'::regclass);


--
-- Name: towers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.towers ALTER COLUMN id SET DEFAULT nextval('public.towers_id_seq'::regclass);


--
-- Name: traffic_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.traffic_logs ALTER COLUMN id SET DEFAULT nextval('public.traffic_logs_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alerts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alerts (id, device_type, device_name, device_ip, message, "timestamp") FROM stdin;
\.


--
-- Data for Name: baselines; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.baselines (id, device_id, metric_type, hour_of_day, day_of_week, avg_value, std_dev, sample_count, last_updated) FROM stdin;
4	\N	synthetic_8.8.8.8	16	-1	21.25	0.4330127018922193	4	2025-12-27 02:04:03.465362
9	\N	synthetic_https://www.cloudflare.com	0	-1	63	0	1	2025-12-27 02:04:03.468486
7	\N	synthetic_https://www.cloudflare.com	1	-1	60.23076923076923	2.422771653542095	13	2025-12-27 02:04:03.469754
1	\N	synthetic_8.8.8.8	15	-1	17	0	1	2025-12-27 02:04:03.471625
6	\N	synthetic_https://www.google.com	16	-1	25.25	1.0897247358851685	4	2025-12-27 02:04:03.472921
3	\N	synthetic_https://www.cloudflare.com	15	-1	21	0	1	2025-12-27 02:04:03.47425
5	\N	synthetic_https://www.cloudflare.com	16	-1	24.25	0.82915619758885	4	2025-12-27 02:04:03.47544
8	\N	synthetic_8.8.8.8	1	-1	21.923076923076923	1.4390989949130542	13	2025-12-27 02:04:03.476658
10	\N	synthetic_https://www.google.com	0	-1	66	0	1	2025-12-27 02:04:03.477832
11	\N	synthetic_8.8.8.8	0	-1	21	0	1	2025-12-27 02:04:03.479022
2	\N	synthetic_https://www.google.com	15	-1	22	0	1	2025-12-27 02:04:03.48018
12	\N	synthetic_https://www.google.com	1	-1	58.53846153846154	11.559979934873354	13	2025-12-27 02:04:03.481414
\.


--
-- Data for Name: equipments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.equipments (id, name, ip, tower_id, is_panel, associated_clients, parent_id, is_online, last_checked, last_latency, maintenance_until, ssh_user, ssh_password, ssh_port, snmp_community, snmp_version, snmp_port, snmp_interface_index, is_mikrotik, mikrotik_interface, api_port, brand, equipment_type, signal_dbm, ccq, connected_clients, last_traffic_in, last_traffic_out) FROM stdin;
\.


--
-- Data for Name: latency_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.latency_history (id, equipment_id, latency, packet_loss, "timestamp") FROM stdin;
\.


--
-- Data for Name: monitor_targets; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.monitor_targets (id, name, target, type, enabled) FROM stdin;
\.


--
-- Data for Name: network_links; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.network_links (id, source_tower_id, target_tower_id, type) FROM stdin;
\.


--
-- Data for Name: parameters; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.parameters (key, value) FROM stdin;
telegram_chat_id	-1003601324129
telegram_token	
telegram_backup_chat_id	
telegram_template_down	🔴 [Device.Name] caiu! IP=[Device.IP]
telegram_template_up	🟢 [Device.Name] voltou! IP=[Device.IP]
telegram_enabled	true
whatsapp_enabled	true
whatsapp_target	
whatsapp_target_group	120363406257973793@g.us
notify_equipment_status	true
notify_backups	true
notify_agent	true
\.


--
-- Data for Name: ping_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ping_logs (id, device_type, device_id, status, latency_ms, "timestamp") FROM stdin;
\.


--
-- Data for Name: ping_stats_hourly; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ping_stats_hourly (id, device_type, device_id, avg_latency_ms, pkt_loss_percent, availability_percent, "timestamp") FROM stdin;
\.


--
-- Data for Name: synthetic_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.synthetic_logs (id, target, test_type, latency_ms, jitter_ms, status_code, success, "timestamp") FROM stdin;
1	8.8.8.8	dns	17	\N	\N	t	2025-12-26 15:58:24.262112
2	https://www.google.com	http	22	\N	\N	t	2025-12-26 15:58:24.270263
3	https://www.cloudflare.com	http	21	\N	\N	t	2025-12-26 15:58:24.27192
4	8.8.8.8	dns	22	\N	\N	t	2025-12-26 16:33:05.068277
5	https://www.google.com	http	27	\N	\N	t	2025-12-26 16:33:05.074073
6	https://www.cloudflare.com	http	25	\N	\N	t	2025-12-26 16:33:05.075711
7	8.8.8.8	dns	21	\N	\N	t	2025-12-26 16:41:36.252101
8	https://www.google.com	http	24	\N	\N	t	2025-12-26 16:41:36.256763
9	https://www.cloudflare.com	http	25	\N	\N	t	2025-12-26 16:41:36.258102
10	8.8.8.8	dns	21	\N	\N	t	2025-12-26 16:46:37.370117
11	https://www.google.com	http	25	\N	\N	t	2025-12-26 16:46:37.37355
12	https://www.cloudflare.com	http	23	\N	\N	t	2025-12-26 16:46:37.374944
13	8.8.8.8	dns	21	\N	\N	t	2025-12-26 16:55:27.258479
14	https://www.google.com	http	25	\N	\N	t	2025-12-26 16:55:27.26381
15	https://www.cloudflare.com	http	24	\N	\N	t	2025-12-26 16:55:27.265518
16	8.8.8.8	dns	21	\N	\N	t	2025-12-27 00:56:15.385298
17	https://www.google.com	http	66	\N	\N	t	2025-12-27 00:56:15.393869
18	https://www.cloudflare.com	http	63	\N	\N	t	2025-12-27 00:56:15.395517
19	8.8.8.8	dns	20	\N	\N	t	2025-12-27 01:01:16.583143
20	https://www.google.com	http	53	\N	\N	t	2025-12-27 01:01:16.585555
21	https://www.cloudflare.com	http	61	\N	\N	t	2025-12-27 01:01:16.587115
22	8.8.8.8	dns	23	\N	\N	t	2025-12-27 01:06:17.771727
23	https://www.google.com	http	64	\N	\N	t	2025-12-27 01:06:17.774745
24	https://www.cloudflare.com	http	62	\N	\N	t	2025-12-27 01:06:17.776134
25	8.8.8.8	dns	23	\N	\N	t	2025-12-27 01:11:18.971243
26	https://www.google.com	http	63	\N	\N	t	2025-12-27 01:11:18.975445
27	https://www.cloudflare.com	http	61	\N	\N	t	2025-12-27 01:11:18.976983
28	8.8.8.8	dns	23	\N	\N	t	2025-12-27 01:16:20.177354
29	https://www.google.com	http	67	\N	\N	t	2025-12-27 01:16:20.179616
30	https://www.cloudflare.com	http	57	\N	\N	t	2025-12-27 01:16:20.18113
31	8.8.8.8	dns	23	\N	\N	t	2025-12-27 01:21:21.373833
32	https://www.google.com	http	67	\N	\N	t	2025-12-27 01:21:21.377321
33	https://www.cloudflare.com	http	54	\N	\N	t	2025-12-27 01:21:21.378633
34	8.8.8.8	dns	21	\N	\N	t	2025-12-27 01:26:22.562324
35	https://www.google.com	http	54	\N	\N	t	2025-12-27 01:26:22.564181
36	https://www.cloudflare.com	http	61	\N	\N	t	2025-12-27 01:26:22.565351
37	8.8.8.8	dns	22	\N	\N	t	2025-12-27 01:34:43.111281
38	https://www.google.com	http	62	\N	\N	t	2025-12-27 01:34:43.115895
39	https://www.cloudflare.com	http	64	\N	\N	t	2025-12-27 01:34:43.117244
40	8.8.8.8	dns	22	\N	\N	t	2025-12-27 01:39:44.311508
41	https://www.google.com	http	65	\N	\N	t	2025-12-27 01:39:44.315922
42	https://www.cloudflare.com	http	60	\N	\N	t	2025-12-27 01:39:44.317532
43	8.8.8.8	dns	23	\N	\N	t	2025-12-27 01:44:45.512079
44	https://www.google.com	http	63	\N	\N	t	2025-12-27 01:44:45.515156
45	https://www.cloudflare.com	http	62	\N	\N	t	2025-12-27 01:44:45.516773
46	8.8.8.8	dns	22	\N	\N	t	2025-12-27 01:49:38.004857
47	https://www.google.com	http	65	\N	\N	t	2025-12-27 01:49:38.00963
48	https://www.cloudflare.com	http	62	\N	\N	t	2025-12-27 01:49:38.010899
49	8.8.8.8	dns	22	\N	\N	t	2025-12-27 01:50:09.99631
50	https://www.google.com	http	23	\N	\N	t	2025-12-27 01:50:10.002541
51	https://www.cloudflare.com	http	60	\N	\N	t	2025-12-27 01:50:10.004266
52	8.8.8.8	dns	18	\N	\N	t	2025-12-27 01:54:56.070375
53	https://www.google.com	http	50	\N	\N	t	2025-12-27 01:54:56.07663
54	https://www.cloudflare.com	http	59	\N	\N	t	2025-12-27 01:54:56.07834
55	8.8.8.8	dns	23	\N	\N	t	2025-12-27 01:59:57.285071
56	https://www.google.com	http	65	\N	\N	t	2025-12-27 01:59:57.288775
57	https://www.cloudflare.com	http	60	\N	\N	t	2025-12-27 01:59:57.290132
58	8.8.8.8	dns	22	\N	\N	t	2025-12-27 02:04:04.604486
59	https://www.google.com	http	67	\N	\N	t	2025-12-27 02:04:04.610534
60	https://www.cloudflare.com	http	22	\N	\N	t	2025-12-27 02:04:04.612075
61	8.8.8.8	dns	21	\N	\N	t	2025-12-27 02:09:05.802855
62	https://www.google.com	http	55	\N	\N	t	2025-12-27 02:09:05.807099
63	https://www.cloudflare.com	http	57	\N	\N	t	2025-12-27 02:09:05.808737
\.


--
-- Data for Name: tower_requests; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tower_requests (id, name, ip, latitude, longitude, requested_by, created_at, status) FROM stdin;
\.


--
-- Data for Name: towers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.towers (id, name, ip, latitude, longitude, observations, is_online, last_checked, parent_id, maintenance_until) FROM stdin;
1	TORRE TESTE 1	\N	-19.54592838385575	-54.04321564181564		f	2025-12-27 01:14:29.901347	\N	\N
\.


--
-- Data for Name: traffic_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.traffic_logs (id, equipment_id, in_mbps, out_mbps, "timestamp") FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, name, email, hashed_password, role, created_at, last_latitude, last_longitude, last_location_update) FROM stdin;
1	Admin	diegojlc22@gmail.com	$2b$12$t8DIvZMKZ858WqP.VslnPevMz1mR9h4vNW8EhPxbsie2kMqMy0tu2	admin	2025-12-26 15:58:28.328127	-19.515475	-54.0439633	2025-12-27 03:03:07.062613
\.


--
-- Name: alerts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.alerts_id_seq', 1, false);


--
-- Name: baselines_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.baselines_id_seq', 12, true);


--
-- Name: equipments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.equipments_id_seq', 1, false);


--
-- Name: latency_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.latency_history_id_seq', 1, false);


--
-- Name: monitor_targets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.monitor_targets_id_seq', 1, false);


--
-- Name: network_links_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.network_links_id_seq', 1, false);


--
-- Name: ping_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ping_logs_id_seq', 1, false);


--
-- Name: ping_stats_hourly_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ping_stats_hourly_id_seq', 1, false);


--
-- Name: synthetic_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.synthetic_logs_id_seq', 63, true);


--
-- Name: tower_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tower_requests_id_seq', 1, false);


--
-- Name: towers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.towers_id_seq', 1, true);


--
-- Name: traffic_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.traffic_logs_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: alerts alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_pkey PRIMARY KEY (id);


--
-- Name: baselines baselines_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.baselines
    ADD CONSTRAINT baselines_pkey PRIMARY KEY (id);


--
-- Name: equipments equipments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipments
    ADD CONSTRAINT equipments_pkey PRIMARY KEY (id);


--
-- Name: latency_history latency_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.latency_history
    ADD CONSTRAINT latency_history_pkey PRIMARY KEY (id);


--
-- Name: monitor_targets monitor_targets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monitor_targets
    ADD CONSTRAINT monitor_targets_pkey PRIMARY KEY (id);


--
-- Name: network_links network_links_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.network_links
    ADD CONSTRAINT network_links_pkey PRIMARY KEY (id);


--
-- Name: parameters parameters_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parameters
    ADD CONSTRAINT parameters_pkey PRIMARY KEY (key);


--
-- Name: ping_logs ping_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ping_logs
    ADD CONSTRAINT ping_logs_pkey PRIMARY KEY (id);


--
-- Name: ping_stats_hourly ping_stats_hourly_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ping_stats_hourly
    ADD CONSTRAINT ping_stats_hourly_pkey PRIMARY KEY (id);


--
-- Name: synthetic_logs synthetic_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.synthetic_logs
    ADD CONSTRAINT synthetic_logs_pkey PRIMARY KEY (id);


--
-- Name: tower_requests tower_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tower_requests
    ADD CONSTRAINT tower_requests_pkey PRIMARY KEY (id);


--
-- Name: towers towers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.towers
    ADD CONSTRAINT towers_pkey PRIMARY KEY (id);


--
-- Name: traffic_logs traffic_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.traffic_logs
    ADD CONSTRAINT traffic_logs_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_equipments_ip; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_equipments_ip ON public.equipments USING btree (ip);


--
-- Name: idx_equipments_is_online; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_equipments_is_online ON public.equipments USING btree (is_online);


--
-- Name: idx_equipments_tower_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_equipments_tower_id ON public.equipments USING btree (tower_id) WHERE (tower_id IS NOT NULL);


--
-- Name: idx_equipments_tower_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_equipments_tower_status ON public.equipments USING btree (tower_id, is_online) WHERE (tower_id IS NOT NULL);


--
-- Name: idx_equipments_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_equipments_type ON public.equipments USING btree (equipment_type);


--
-- Name: idx_ping_logs_brin_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ping_logs_brin_timestamp ON public.ping_logs USING brin ("timestamp") WITH (pages_per_range='128');


--
-- Name: idx_ping_logs_device; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ping_logs_device ON public.ping_logs USING btree (device_type, device_id, "timestamp" DESC);


--
-- Name: idx_ping_logs_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ping_logs_timestamp ON public.ping_logs USING btree ("timestamp");


--
-- Name: idx_towers_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_towers_name ON public.towers USING btree (name);


--
-- Name: idx_traffic_logs_equipment; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_traffic_logs_equipment ON public.traffic_logs USING btree (equipment_id, "timestamp" DESC);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: ix_alerts_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_alerts_id ON public.alerts USING btree (id);


--
-- Name: ix_baselines_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_baselines_device_id ON public.baselines USING btree (device_id);


--
-- Name: ix_baselines_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_baselines_id ON public.baselines USING btree (id);


--
-- Name: ix_equipments_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_equipments_id ON public.equipments USING btree (id);


--
-- Name: ix_equipments_ip; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_equipments_ip ON public.equipments USING btree (ip);


--
-- Name: ix_equipments_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_equipments_name ON public.equipments USING btree (name);


--
-- Name: ix_latency_history_equipment_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_latency_history_equipment_id ON public.latency_history USING btree (equipment_id);


--
-- Name: ix_latency_history_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_latency_history_id ON public.latency_history USING btree (id);


--
-- Name: ix_latency_history_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_latency_history_timestamp ON public.latency_history USING btree ("timestamp");


--
-- Name: ix_monitor_targets_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_monitor_targets_id ON public.monitor_targets USING btree (id);


--
-- Name: ix_monitor_targets_target; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_monitor_targets_target ON public.monitor_targets USING btree (target);


--
-- Name: ix_network_links_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_network_links_id ON public.network_links USING btree (id);


--
-- Name: ix_ping_logs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ping_logs_id ON public.ping_logs USING btree (id);


--
-- Name: ix_ping_stats_hourly_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ping_stats_hourly_device_id ON public.ping_stats_hourly USING btree (device_id);


--
-- Name: ix_ping_stats_hourly_device_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ping_stats_hourly_device_type ON public.ping_stats_hourly USING btree (device_type);


--
-- Name: ix_ping_stats_hourly_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ping_stats_hourly_id ON public.ping_stats_hourly USING btree (id);


--
-- Name: ix_ping_stats_hourly_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ping_stats_hourly_timestamp ON public.ping_stats_hourly USING btree ("timestamp");


--
-- Name: ix_synthetic_logs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_synthetic_logs_id ON public.synthetic_logs USING btree (id);


--
-- Name: ix_synthetic_logs_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_synthetic_logs_timestamp ON public.synthetic_logs USING btree ("timestamp");


--
-- Name: ix_tower_requests_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tower_requests_id ON public.tower_requests USING btree (id);


--
-- Name: ix_towers_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_towers_id ON public.towers USING btree (id);


--
-- Name: ix_towers_ip; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_towers_ip ON public.towers USING btree (ip);


--
-- Name: ix_towers_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_towers_name ON public.towers USING btree (name);


--
-- Name: ix_traffic_logs_equipment_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_traffic_logs_equipment_id ON public.traffic_logs USING btree (equipment_id);


--
-- Name: ix_traffic_logs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_traffic_logs_id ON public.traffic_logs USING btree (id);


--
-- Name: ix_traffic_logs_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_traffic_logs_timestamp ON public.traffic_logs USING btree ("timestamp");


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: equipments equipments_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipments
    ADD CONSTRAINT equipments_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.equipments(id);


--
-- Name: equipments equipments_tower_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipments
    ADD CONSTRAINT equipments_tower_id_fkey FOREIGN KEY (tower_id) REFERENCES public.towers(id);


--
-- Name: network_links network_links_source_tower_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.network_links
    ADD CONSTRAINT network_links_source_tower_id_fkey FOREIGN KEY (source_tower_id) REFERENCES public.towers(id);


--
-- Name: network_links network_links_target_tower_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.network_links
    ADD CONSTRAINT network_links_target_tower_id_fkey FOREIGN KEY (target_tower_id) REFERENCES public.towers(id);


--
-- Name: traffic_logs traffic_logs_equipment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.traffic_logs
    ADD CONSTRAINT traffic_logs_equipment_id_fkey FOREIGN KEY (equipment_id) REFERENCES public.equipments(id);


--
-- PostgreSQL database dump complete
--

\unrestrict qUAuy3CWKWfTUiTsfoIG7N6FjzHgspqo2KsYFnWsebcRl7IcNob1GTa79GtcV4a

