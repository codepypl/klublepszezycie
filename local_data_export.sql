--
-- PostgreSQL database dump
--

\restrict ceVgrd761HiXI806R51VUrzpYe0tQXMWNZ9wQBCcmae6VnHylwAJYaFnj03q4xj

-- Dumped from database version 15.14 (Postgres.app)
-- Dumped by pg_dump version 15.14 (Postgres.app)

-- Started on 2025-09-01 14:17:47 CEST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 3821 (class 0 OID 25061)
-- Dependencies: 219
-- Data for Name: sections; Type: TABLE DATA; Schema: public; Owner: shadi
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.sections DISABLE TRIGGER ALL;

COPY public.sections (id, name, title, subtitle, content, background_image, pillars_data, final_text, floating_cards_data, "order", is_active, created_at, updated_at, enable_pillars, enable_floating_cards, pillars_count, floating_cards_count) FROM stdin;
1	hero	💡 Chcesz mieć lepsze życie? Dołącz do klubu który zmienia życie w 4 kluczowych obszarach.	Odkryj, jak klub „Lepsze Życie” pomaga poprawić finanse zdrowie, budowac społeczności i opanować narzędzia AI – aby żyć mądrzej i lepiej		static/images/hero/hero-bg.jpg	\N		\N	1	t	2025-08-22 11:37:09.951463	2025-08-22 11:43:43.271136	f	f	4	3
2	benefits	🧭 Czego nauczysz się na prezentacji	Praktyczna wiedza, która zmieni Twoje życie		\N	\N		\N	2	t	2025-08-22 11:37:09.955837	2025-08-22 11:44:16.506088	f	f	4	3
5	cta	🚀 Gotowy na lepsze życie?	Zarezerwuj miejsce w darmowej prezentacji "Lepsze Życie" — i dowiedz się, jak ten klub może pomóc Ci żyć z większym celem, społecznością i nowoczesnymi umiejętnościami.		\N	\N		\N	5	t	2025-08-22 11:37:09.966111	2025-08-22 11:46:24.472743	f	f	4	3
6	faq	❓ Często zadawane pytania	Odpowiedzi na najczęściej zadawane pytania o klub "Lepsze Życie"		\N	\N		\N	6	t	2025-08-22 11:37:09.967851	2025-08-22 11:46:57.101616	f	f	4	3
4	testimonials	💬 Co mówią nasi członkowie 50+	Prawdziwe historie osób, które zmieniły swoje życie dzięki klubowi			\N		\N	4	f	2025-08-22 11:37:09.960389	2025-08-23 19:23:19.392893	f	f	4	3
3	about	🌱 Klub stworzony specjalnie dla Ciebie!		"Lepsze Życie" to więcej niż tylko klub. To społeczność osób, które rozumieją, że życie trzeba brać pełnymi garściami.	static/images/about/community-senior.jpg	[{"icon": "fas fa-coins", "title": "Finanse", "color": "text-warning", "description": "Wi\\u0119ksze dochody, lepsze, bezpieczne \\u017cycie.", "link": "/finanse"}, {"icon": "fas fa-robot", "title": "Narz\\u0119dzia AI", "color": "text-primary", "description": "Wykorzystaj technologi\\u0119 do rozwi\\u0105zywania codziennych problem\\u00f3w.", "link": "/naucz-sie-ai"}, {"icon": "fas fa-hands-helping", "title": "Relacje", "color": "text-success", "description": "Buduj prawdziwe, wspieraj\\u0105ce relacje.", "link": "/relacje"}, {"icon": "fas fa-dumbbell", "title": "Zdrowie", "color": "text-primary", "description": "Przejmij kontrol\\u0119 nad swoim samopoczuciem, krok po kroku", "link": "/zdrowie"}]	Niezależnie od tego, czy zaczynasz od nowa, czy chcesz pójść dalej — nie jesteś sam. Ten klub został zbudowany dla ludzi takich jak Ty.	[{"icon": "fas fa-lightbulb", "title": "Inspiracja", "color": "text-warning", "delay": 300, "link": ""}, {"icon": "fas fa-users", "title": "Wsp\\u00f3lnota", "color": "text-success", "delay": 450, "link": ""}, {"icon": "fas fa-rocket", "title": "Wzrost", "color": "text-secondary", "delay": 700, "link": ""}]	3	t	2025-08-22 11:37:09.958298	2025-08-23 09:22:49.19407	t	t	4	3
\.


ALTER TABLE public.sections ENABLE TRIGGER ALL;

--
-- TOC entry 3835 (class 0 OID 25124)
-- Dependencies: 233
-- Data for Name: benefit_items; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.benefit_items DISABLE TRIGGER ALL;

COPY public.benefit_items (id, section_id, title, description, icon, image, "order", is_active, created_at, updated_at) FROM stdin;
1	\N	Jak zwiększyć swoje dochody		fas fa-gift	static/images/benefits/e72ed8260e214e41a0cf227f86fc16f2.jpg	1	t	2025-08-22 11:37:09.973382	2025-08-23 08:59:05.899226
3	\N	Społeczność & Przeciwdziałanie Samotności		fas fa-hands-helping	static/images/benefits/community-senior.jpg	3	t	2025-08-22 11:37:09.983329	2025-08-23 09:03:28.686019
4	\N	Zdrowie & Witalność		fas fa-heart	static/images/benefits/health-senior.jpg	4	t	2025-08-22 11:37:09.987662	2025-08-23 09:03:36.473256
2	\N	 Lepsze życie dzięki AI		fas fa-robot	static/images/benefits/abfc11e80f0048ed908d8b794d07e6b0.jpg	2	t	2025-08-22 11:37:09.977426	2025-08-23 16:31:58.801822
\.


ALTER TABLE public.benefit_items ENABLE TRIGGER ALL;

--
-- TOC entry 3839 (class 0 OID 33245)
-- Dependencies: 237
-- Data for Name: email_templates; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.email_templates DISABLE TRIGGER ALL;

COPY public.email_templates (id, name, subject, html_content, text_content, template_type, variables, is_active, created_at, updated_at) FROM stdin;
9	event_reminder_24h_before	Przypomnienie: {{event_title}} - jutro o {{event_date}}	\n<!DOCTYPE html>\n<html lang="pl">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Przypomnienie o wydarzeniu</title>\n</head>\n<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">\n    <div style="text-align: center; margin-bottom: 30px;">\n        <h1 style="color: #007bff; margin-bottom: 10px;">📅 Przypomnienie o wydarzeniu</h1>\n        <p style="font-size: 18px; color: #666;">Jutro spotykamy się na wydarzeniu!</p>\n    </div>\n    \n    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">\n        <h2 style="color: #28a745; margin-top: 0;">Cześć {{name}}!</h2>\n        <p>Przypominamy o jutrzejszym wydarzeniu:</p>\n        \n        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">\n            <h3 style="color: #155724; margin-top: 0;">🎯 {{event_title}}</h3>\n                            <p><strong>Data:</strong> {{event_date}}</p>\n                            <p><strong>Typ:</strong> {{event_type}}</p>\n                            {% if meeting_link %}\n                            <p><strong>Link do spotkania:</strong> <a href="{{meeting_link}}" style="color: #155724;">{{meeting_link}}</a></p>\n                            {% endif %}\n                            {% if location %}\n                            <p><strong>Miejsce:</strong> {{location}}</p>\n                            {% endif %}\n        </div>\n        \n        <p>Do zobaczenia jutro!</p>\n    </div>\n    \n    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">\n        <p style="color: #666; font-size: 14px;">\n            Z poważaniem,<br>\n            Zespół Klubu Lepsze Życie\n        </p>\n    </div>\n</body>\n</html>\n            	Przypomnienie o jutrzejszym wydarzeniu: {{event_title}} - {{event_date}}	event_reminder_24h_before	["name", "event_title", "event_date", "event_type", "meeting_link", "location"]	t	2025-08-26 10:32:37.861124	2025-08-26 10:32:37.86113
10	event_reminder_1h_before	🔔 Za godzinę: {{event_title}}	\n<!DOCTYPE html>\n<html lang="pl">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Wydarzenie za godzinę</title>\n</head>\n<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">\n    <div style="text-align: center; margin-bottom: 30px;">\n        <h1 style="color: #ffc107; margin-bottom: 10px;">🔔 Wydarzenie za godzinę!</h1>\n        <p style="font-size: 18px; color: #666;">Przygotuj się na spotkanie</p>\n    </div>\n    \n    <div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">\n        <h2 style="color: #856404; margin-top: 0;">Cześć {{name}}!</h2>\n        <p>Za godzinę rozpoczyna się wydarzenie:</p>\n        \n        <div style="background-color: #fff; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">\n            <h3 style="color: #856404; margin-top: 0;">🎯 {{event_title}}</h3>\n                            <p><strong>Data:</strong> {{event_date}}</p>\n                            <p><strong>Typ:</strong> {{event_type}}</p>\n                            {% if meeting_link %}\n                            <p><strong>Link do spotkania:</strong> <a href="{{meeting_link}}" style="color: #856404;">{{meeting_link}}</a></p>\n                            {% endif %}\n                            {% if location %}\n                            <p><strong>Miejsce:</strong> {{location}}</p>\n                            {% endif %}\n        </div>\n        \n        <p><strong>Przygotuj się:</strong></p>\n        <ul style="text-align: left;">\n            <li>Sprawdź czy masz wszystkie potrzebne materiały</li>\n            <li>Upewnij się, że Twój sprzęt działa</li>\n            <li>Przyjdź 5 minut wcześniej</li>\n        </ul>\n    </div>\n    \n    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">\n        <p style="color: #666; font-size: 14px;">\n            Do zobaczenia za godzinę!<br>\n            Zespół Klubu Lepsze Życie\n        </p>\n    </div>\n</body>\n</html>\n            	Wydarzenie za godzinę: {{event_title}} - {{event_date}}	event_reminder_1h_before	["name", "event_title", "event_date", "event_type", "meeting_link", "location"]	t	2025-08-26 10:32:37.865359	2025-08-26 10:32:37.865365
23	Potwierdzenie Zapisu na Wydarzenie	✅ Potwierdzenie zapisu na wydarzenie: {{event_name}}	\n<!DOCTYPE html>\n<html lang="pl">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Potwierdzenie Zapisu na Wydarzenie</title>\n</head>\n<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">\n    <div style="text-align: center; margin-bottom: 30px;">\n        <h1 style="color: #28a745; margin-bottom: 10px;">✅ Potwierdzenie zapisu</h1>\n        <p style="font-size: 18px; color: #666;">Twoje miejsce zostało zarezerwowane!</p>\n    </div>\n    \n    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">\n        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>\n        <p>Potwierdzamy zapis na wydarzenie <strong>{{event_name}}</strong>, które odbędzie się dnia <strong>{{event_start_date}}</strong> o godzinie <strong>{{event_start_hour}}</strong>.</p>\n        \n        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">\n            <h3 style="color: #155724; margin-top: 0;">📅 Co dalej?</h3>\n            <p style="margin-bottom: 10px;">Otrzymasz od nas przypomnienie o wydarzeniu tak byś mógł się odpowiednio wcześniej przygotować.</p>\n        </div>\n    </div>\n    \n    <div style="background-color: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 5px; padding: 15px; margin: 20px 0;">\n        <h3 style="color: #0056b3; margin-top: 0;">🤔 Czy wiesz że...</h3>\n        <p style="margin-bottom: 15px;">Możesz od nas automatycznie otrzymywać informacje na swój e-mail o nowych wydarzeniach, które będą się wydarzać w Klubie?</p>\n        <p style="margin-bottom: 10px;">Wystarczy, że zalogujesz się w swoim panelu <a href="{{user_panel_url}}" style="color: #0056b3;">{{user_panel_url}}</a> i oznaczysz opcję "dołącz do klubu".</p>\n    </div>\n    \n    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">\n        <h3 style="color: #856404; margin-top: 0;">🎁 Co zyskasz dołączając do klubu:</h3>\n        <ul style="text-align: left; margin: 0; padding-left: 20px;">\n            <li>Otrzymasz przypomnienie o wydarzeniu na 24h przed</li>\n            <li>Będziesz informowany o nowych wydarzeniach i webinarach</li>\n            <li>Dostaniesz dostęp do ekskluzywnych materiałów</li>\n        </ul>\n    </div>\n    \n    <div style="background-color: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 5px; padding: 15px; margin: 20px 0;">\n        <h3 style="color: #0056b3; margin-top: 0;">🔑 Twoje dane logowania</h3>\n        <p style="margin-bottom: 15px;"><strong>Email:</strong> {{email}}</p>\n        <p style="margin-bottom: 15px;"><strong>Tymczasowe hasło:</strong> <span style="background-color: #f8f9fa; padding: 5px 10px; border-radius: 5px; font-family: monospace; font-size: 16px;">{{temp_password}}</span></p>\n        <p style="margin-bottom: 10px; color: #0056b3;"><strong>⚠️ WAŻNE:</strong> Przy pierwszym logowaniu musisz zmienić to hasło na własne!</p>\n        <div style="text-align: center; margin-top: 20px;">\n            <a href="{{ url_for('user_login', _external=True) }}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; display: inline-block; font-weight: bold;">Zaloguj się teraz</a>\n        </div>\n    </div>\n    \n    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">\n        <p style="color: #666; font-size: 14px;">\n            Z poważaniem,<br>\n            <strong>Zespół Klubu Lepsze Życie</strong>\n        </p>\n        <p style="color: #999; font-size: 12px; margin-top: 20px;">\n            Ten email został wysłany na adres {{email}}\n        </p>\n    </div>\n</body>\n</html>\n        	\n✅ Potwierdzenie zapisu na wydarzenie\n\nCześć {{name}}!\n\nPotwierdzamy zapis na wydarzenie {{event_name}}, które odbędzie się dnia {{event_start_date}} o godzinie {{event_start_hour}}.\n\n📅 Co dalej?\nOtrzymasz od nas przypomnienie o wydarzeniu tak byś mógł się odpowiednio wcześniej przygotować.\n\n🤔 Czy wiesz że...\nMożesz od nas automatycznie otrzymywać informacje na swój e-mail o nowych wydarzeniach, które będą się wydarzać w Klubie?\n\nWystarczy, że zalogujesz się w swoim panelu {{user_panel_url}} i oznaczysz opcję "dołącz do klubu".\n\n🎁 Co zyskasz dołączając do klubu:\n- Otrzymasz przypomnienie o wydarzeniu na 24h przed\n- Będziesz informowany o nowych wydarzeniach i webinarach\n- Dostaniesz dostęp do ekskluzywnych materiałów\n\n🔑 TWOJE DANE LOGOWANIA:\nEmail: {{email}}\nTymczasowe hasło: {{temp_password}}\n\n⚠️ WAŻNE: Przy pierwszym logowaniu musisz zmienić to hasło na własne!\n\nZ poważaniem,\nZespół Klubu Lepsze Życie\n\nTen email został wysłany na adres {{email}}\n        	event_confirmation	["name", "email", "event_name", "event_start_date", "event_start_hour", "temp_password", "user_panel_url"]	t	2025-08-28 15:47:01.476575	2025-08-28 16:17:30.362504
11	event_reminder_5min_before	🚀 {{event_title}} rozpoczyna się za 5 minut!	\n<!DOCTYPE html>\n<html lang="pl">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Wydarzenie za 5 minut</title>\n</head>\n<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">\n    <div style="text-align: center; margin-bottom: 30px;">\n        <h1 style="color: #dc3545; margin-bottom: 10px;">🚀 Wydarzenie za 5 minut!</h1>\n        <p style="font-size: 18px; color: #666;">Czas dołączyć do spotkania</p>\n    </div>\n    \n    <div style="background-color: #f8d7da; padding: 20px; border-radius: 10px; margin-bottom: 20px;">\n        <h2 style="color: #721c24; margin-top: 0;">Cześć {{name}}!</h2>\n        <p>Wydarzenie rozpoczyna się za 5 minut:</p>\n        \n        <div style="background-color: #fff; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">\n            <h3 style="color: #721c24; margin-top: 0;">🎯 {{event_title}}</h3>\n                            <p><strong>Data:</strong> {{event_date}}</p>\n                            <p><strong>Typ:</strong> {{event_type}}</p>\n                            {% if meeting_link %}\n                            <p><strong>Link do spotkania:</strong> <a href="{{meeting_link}}" style="color: #721c24; font-weight: bold;">{{meeting_link}}</a></p>\n                            {% endif %}\n                            {% if location %}\n                            <p><strong>Miejsce:</strong> {{location}}</p>\n                            {% endif %}\n        </div>\n        \n        <div style="text-align: center; margin: 20px 0;">\n                            {% if meeting_link %}\n                            <a href="{{meeting_link}}" style="background-color: #dc3545; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-size: 18px; font-weight: bold;">\n                                🚀 DOŁĄCZ TERAZ\n                            </a>\n                            {% endif %}\n        </div>\n        \n        <p><strong>Ostatnie przygotowania:</strong></p>\n        <ul style="text-align: left;">\n            <li>Sprawdź połączenie internetowe</li>\n            <li>Uruchom aplikację do spotkań</li>\n            <li>Przygotuj notatnik</li>\n        </ul>\n    </div>\n    \n    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">\n        <p style="color: #666; font-size: 14px;">\n            Do zobaczenia za chwilę!<br>\n            Zespół Klubu Lepsze Życie\n        </p>\n    </div>\n</body>\n</html>\n            	Wydarzenie za 5 minut: {{event_title}} - {{event_date}}	event_reminder_5min_before	["name", "event_title", "event_date", "event_type", "meeting_link", "location"]	t	2025-08-26 10:32:37.866801	2025-08-26 10:32:37.866805
12	Email Powitalny	Witamy w Klubie Lepsze Życie! 🎉	\n<!DOCTYPE html>\n<html lang="pl">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Witamy w Klubie Lepsze Życie</title>\n</head>\n<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">\n    <div style="text-align: center; margin-bottom: 30px;">\n        <h1 style="color: #28a745; margin-bottom: 10px;">🎉 Witamy w Klubie Lepsze Życie!</h1>\n        <p style="font-size: 18px; color: #666;">Cieszę się, że dołączyłeś do nas!</p>\n    </div>\n    \n    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">\n        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>\n        <p>Dziękujemy za zarejestrowanie się na naszą darmową prezentację. Twoje miejsce zostało zarezerwowane!</p>\n        \n        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">\n            <h3 style="color: #155724; margin-top: 0;">📅 Co dalej?</h3>\n            <ul style="text-align: left; margin: 0; padding-left: 20px;">\n                <li>Otrzymasz przypomnienie o wydarzeniu na 24h przed</li>\n                <li>Będziesz informowany o nowych wydarzeniach i webinarach</li>\n                <li>Dostaniesz dostęp do ekskluzywnych materiałów</li>\n            </ul>\n        </div>\n    </div>\n    \n    <div style="background-color: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 5px; padding: 15px; margin: 20px 0;">\n        <h3 style="color: #0056b3; margin-top: 0;">🔑 Twoje dane logowania</h3>\n        <p style="margin-bottom: 15px;"><strong>Email:</strong> {{email}}</p>\n        <p style="margin-bottom: 15px;"><strong>Tymczasowe hasło:</strong> <span style="background-color: #f8f9fa; padding: 5px 10px; border-radius: 5px; font-family: monospace; font-size: 16px;">{{temp_password}}</span></p>\n        <p style="margin-bottom: 10px; color: #0056b3;"><strong>⚠️ WAŻNE:</strong> Przy pierwszym logowaniu musisz zmienić to hasło na własne!</p>\n        <div style="text-align: center; margin-top: 20px;">\n            <a href="{{ url_for('user_login', _external=True) }}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; display: inline-block; font-weight: bold;">Zaloguj się teraz</a>\n        </div>\n    </div>\n    \n    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">\n        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>\n        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>\n        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>\n        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>\n    </div>\n    \n    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">\n        <p style="color: #666; font-size: 14px;">\n            Z poważaniem,<br>\n            <strong>Zespół Klubu Lepsze Życie</strong>\n        </p>\n        <p style="color: #999; font-size: 12px; margin-top: 20px;">\n            Ten email został wysłany na adres {{email}}\n        </p>\n    </div>\n</body>\n</html>\n            	\nWitamy w Klubie Lepsze Życie! 🎉\n\nCześć {{name}}!\n\nDziękujemy za zarejestrowanie się na naszą darmową prezentację. Twoje miejsce zostało zarezerwowane!\n\nCo dalej?\n- Otrzymasz przypomnienie o wydarzeniu na 24h przed\n- Będziesz informowany o nowych wydarzeniach i webinarach\n- Dostaniesz dostęp do ekskluzywnych materiałów\n\n🔑 TWOJE DANE LOGOWANIA:\nEmail: {{email}}\nTymczasowe hasło: {{temp_password}}\n\n⚠️ WAŻNE: Przy pierwszym logowaniu musisz zmienić to hasło na własne!\n\nTwoje dane są bezpieczne - możesz w każdej chwili:\n- Zrezygnować z subskrypcji: {{unsubscribe_url}}\n- Usunąć swoje konto: {{delete_account_url}}\n\nZ poważaniem,\nZespół Klubu Lepsze Życie\n\nTen email został wysłany na adres {{email}}\n            	welcome	["name", "email", "temp_password", "unsubscribe_url", "delete_account_url"]	t	2025-08-26 10:37:38.884524	2025-08-28 16:17:30.414932
14	Powiadomienie dla Administratora	🔔 Nowa rejestracja w Klubie Lepsze Życie	<!DOCTYPE html>\n<html lang="pl">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Nowa Rejestracja</title>\n</head>\n<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">\n    <div style="text-align: center; margin-bottom: 30px;">\n        <h1 style="color: #28a745; margin-bottom: 10px;">🔔 Nowa Rejestracja w Klubie</h1>\n        <p style="font-size: 18px; color: #666;">Pojawił się nowy członek!</p>\n    </div>\n\n    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">\n        <h2 style="color: #007bff; margin-top: 0;">Cześć {{admin_name}}!</h2>\n        <p>W systemie pojawiła się nowa rejestracja:</p>\n\n        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">\n            <h3 style="color: #155724; margin-top: 0;">👤 Nowy Członek</h3>\n            <p style="margin: 5px 0;"><strong>Imię:</strong> {{new_member_name}}</p>\n            <p style="margin: 5px 0;"><strong>Email:</strong> {{new_member_email}}</p>\n            <p style="margin: 5px 0;"><strong>Data rejestracji:</strong> {{registration_date}}</p>\n        </div>\n    </div>\n\n    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">\n        <p style="color: #666; font-size: 14px;">\n            Z poważaniem,<br>\n            <strong>System Klubu Lepsze Życie</strong>\n        </p>\n    </div>\n</body>\n</html>	\nNowa Rejestracja w Klubie\n\nCześć {{admin_name}}!\n\nW systemie pojawiła się nowa rejestracja:\n\n👤 Nowy Członek\nImię: {{new_member_name}}\nEmail: {{new_member_email}}\nData rejestracji: {{registration_date}}\n\nZ poważaniem,\nSystem Klubu Lepsze Życie\n                	admin_notification	admin_name,new_member_name,new_member_email,registration_date	t	2025-08-26 10:37:38.891001	2025-08-29 13:30:28.965476
\.


ALTER TABLE public.email_templates ENABLE TRIGGER ALL;

--
-- TOC entry 3857 (class 0 OID 34020)
-- Dependencies: 255
-- Data for Name: email_automations; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.email_automations DISABLE TRIGGER ALL;

COPY public.email_automations (id, name, description, automation_type, template_id, trigger_conditions, is_active, created_at, updated_at) FROM stdin;
1	Automatyczny email powitalny	Automatycznie wysyła email powitalny po rejestracji	welcome	12	{"trigger": "user_registration"}	t	2025-08-26 12:11:06.368005	2025-08-26 12:11:06.368012
2	Przypomnienie o wydarzeniu - 24h_before	Automatycznie wysyła przypomnienie 24h_before przed wydarzeniem	event_reminder	9	{"trigger": "event_reminder", "type": "24h_before"}	t	2025-08-26 12:11:06.393475	2025-08-26 12:11:06.39348
3	Przypomnienie o wydarzeniu - 1h_before	Automatycznie wysyła przypomnienie 1h_before przed wydarzeniem	event_reminder	10	{"trigger": "event_reminder", "type": "1h_before"}	t	2025-08-26 12:11:06.397807	2025-08-26 12:11:06.397812
4	Przypomnienie o wydarzeniu - 5min_before	Automatycznie wysyła przypomnienie 5min_before przed wydarzeniem	event_reminder	11	{"trigger": "event_reminder", "type": "5min_before"}	t	2025-08-26 12:11:06.405607	2025-08-26 12:11:06.405615
5	Automatyczny email powitalny	Automatycznie wysyła email powitalny po rejestracji	welcome	12	{"trigger": "user_registration"}	t	2025-08-26 12:24:47.500404	2025-08-26 12:24:47.500411
6	Przypomnienie o wydarzeniu - 24h_before	Automatycznie wysyła przypomnienie 24h_before przed wydarzeniem	event_reminder	9	{"trigger": "event_reminder", "type": "24h_before"}	t	2025-08-26 12:24:47.526753	2025-08-26 12:24:47.526765
7	Przypomnienie o wydarzeniu - 1h_before	Automatycznie wysyła przypomnienie 1h_before przed wydarzeniem	event_reminder	10	{"trigger": "event_reminder", "type": "1h_before"}	t	2025-08-26 12:24:47.541286	2025-08-26 12:24:47.541294
8	Przypomnienie o wydarzeniu - 5min_before	Automatycznie wysyła przypomnienie 5min_before przed wydarzeniem	event_reminder	11	{"trigger": "event_reminder", "type": "5min_before"}	t	2025-08-26 12:24:47.553861	2025-08-26 12:24:47.553866
\.


ALTER TABLE public.email_automations ENABLE TRIGGER ALL;

--
-- TOC entry 3863 (class 0 OID 34067)
-- Dependencies: 261
-- Data for Name: email_automation_logs; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.email_automation_logs DISABLE TRIGGER ALL;

COPY public.email_automation_logs (id, automation_id, execution_type, recipient_count, success_count, error_count, status, details, started_at, completed_at) FROM stdin;
\.


ALTER TABLE public.email_automation_logs ENABLE TRIGGER ALL;

--
-- TOC entry 3855 (class 0 OID 34011)
-- Dependencies: 253
-- Data for Name: email_campaigns; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.email_campaigns DISABLE TRIGGER ALL;

COPY public.email_campaigns (id, name, subject, html_content, text_content, recipient_groups, custom_emails, status, send_type, scheduled_at, total_recipients, sent_count, failed_count, created_at, updated_at, sent_at) FROM stdin;
\.


ALTER TABLE public.email_campaigns ENABLE TRIGGER ALL;

--
-- TOC entry 3843 (class 0 OID 33269)
-- Dependencies: 241
-- Data for Name: email_logs; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.email_logs DISABLE TRIGGER ALL;

COPY public.email_logs (id, email, template_id, subject, status, error_message, sent_at) FROM stdin;
1	test@example.com	\N	Witamy w Klubie Lepsze Życie! 🎉	failed	(501, b'Could not decode user and password for AUTH LOGIN')	2025-08-24 11:42:23.933998
2	c@c.pl	\N	Witamy w Klubie Lepsze Życie! 🎉	sent	\N	2025-08-24 12:44:31.4412
3	codeitpy@gmail.com	\N	[TEST] Witamy w Klubie Lepsze Życie! 🎉	sent	\N	2025-08-24 12:45:49.688739
4	c@c.pl	\N	Witamy w Klubie Lepsze Życie! 🎉	sent	\N	2025-08-24 13:15:32.407007
5	codeitpy@gmail.com	\N	Witamy w Klubie Lepsze Życie! 🎉	sent	\N	2025-08-24 15:01:01.242018
6	codeitpy@gmail.com	\N	Witamy w Klubie Lepsze Życie! 🎉	sent	\N	2025-08-24 15:10:56.628427
7	admin@lepszezycie.pl	14	🔔 Nowa rejestracja w Klubie Lepsze Życie	sent	\N	2025-08-26 15:17:53.256023
8	admin@lepszezycie.pl	14	🔔 Nowa rejestracja w Klubie Lepsze Życie	sent	\N	2025-08-28 10:58:38.205164
9	codeitpy@gmail.com	12	Witamy w Klubie Lepsze Życie! 🎉	sent	\N	2025-08-28 13:53:40.561183
10	test@example.com	12	Witamy w Klubie Lepsze Życie! 🎉	sent	\N	2025-08-28 14:03:21.753077
11	test2@example.com	12	Witamy w Klubie Lepsze Życie! 🎉	sent	\N	2025-08-28 14:03:34.482572
12	test3@example.com	12	Witamy w Klubie Lepsze Życie! 🎉	sent	\N	2025-08-28 14:05:03.66067
13	codeitpy@gmail.com	12	Witamy w Klubie Lepsze Życie! 🎉	sent	\N	2025-08-28 15:04:06.917566
14	test4@example.com	12	Witamy w Klubie Lepsze Życie! 🎉	sent	\N	2025-08-28 15:25:35.513526
15	test5@example.com	23	✅ Potwierdzenie zapisu na wydarzenie: Test Nowe Wydarzenie	sent	\N	2025-08-28 16:21:47.899583
16	test6@example.com	12	Witamy w Klubie Lepsze Życie! 🎉	sent	\N	2025-08-28 16:22:44.321093
17	codeitpy@gmail.com	23	✅ Potwierdzenie zapisu na wydarzenie: Test Nowe Wydarzenie	sent	\N	2025-08-29 08:41:58.803953
\.


ALTER TABLE public.email_logs ENABLE TRIGGER ALL;

--
-- TOC entry 3853 (class 0 OID 34002)
-- Dependencies: 251
-- Data for Name: user_groups; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.user_groups DISABLE TRIGGER ALL;

COPY public.user_groups (id, name, description, group_type, criteria, is_active, member_count, created_at, updated_at) FROM stdin;
4	Test Group	Grupa testowa dla przypomnień	manual	{}	t	\N	2025-08-29 13:41:37.503099	2025-08-29 13:41:37.503099
5	Test Group	Grupa testowa dla przypomnień	manual	{}	t	\N	2025-08-29 13:45:49.62922	2025-08-29 13:45:49.62922
6	Test Group	Grupa testowa dla przypomnień	manual	{}	t	\N	2025-08-29 13:47:34.769834	2025-08-29 13:47:34.769834
7	Test Group	Grupa testowa dla przypomnień	manual	{}	t	\N	2025-08-29 13:48:27.781722	2025-08-29 13:48:27.781722
8	Test Group	Grupa testowa dla przypomnień	manual	{}	t	\N	2025-08-29 13:50:19.092721	2025-08-29 13:50:19.092721
9	Test Group	Grupa testowa dla przypomnień	manual	{}	t	\N	2025-08-29 13:51:07.943917	2025-08-29 13:51:07.943917
\.


ALTER TABLE public.user_groups ENABLE TRIGGER ALL;

--
-- TOC entry 3859 (class 0 OID 34034)
-- Dependencies: 257
-- Data for Name: email_schedules; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.email_schedules DISABLE TRIGGER ALL;

COPY public.email_schedules (id, name, description, template_id, trigger_type, trigger_conditions, recipient_type, recipient_emails, recipient_group_id, send_type, scheduled_at, status, last_sent, sent_count, created_at, updated_at) FROM stdin;
1	Email powitalny	Automatyczny email powitalny wysyłany gdy konto użytkownika zostanie aktywowane przez administratora	12	user_activation	{"event": "user_activation"}	user	\N	\N	immediate	\N	active	\N	\N	\N	\N
2	Powiadomienie admina o rejestracji	Email wysyłany do administratora gdy ktoś zarejestruje się na wydarzenie z zgodą na newsletter	14	event_registration	{"event": "event_registration", "newsletter_consent": true}	admin	\N	\N	immediate	\N	active	\N	\N	\N	\N
3	Przypomnienie o wydarzeniu - 24h przed	Przypomnienie o wydarzeniu wysyłane 24h przed do osób zapisanych na wydarzenie	9	event_reminder	{"timing": "24h_before", "event_type": "all"}	group	\N	\N	scheduled	\N	active	\N	\N	\N	\N
4	Przypomnienie o wydarzeniu - 1h przed	Przypomnienie o wydarzeniu wysyłane 1h przed do osób zapisanych na wydarzenie	10	event_reminder	{"timing": "1h_before", "event_type": "all"}	group	\N	\N	scheduled	\N	active	\N	\N	\N	\N
5	Przypomnienie o wydarzeniu - 5min przed	Przypomnienie o wydarzeniu wysyłane 5min przed do osób zapisanych na wydarzenie	11	event_reminder	{"timing": "5min_before", "event_type": "all"}	group	\N	\N	scheduled	\N	active	\N	\N	\N	\N
\.


ALTER TABLE public.email_schedules ENABLE TRIGGER ALL;

--
-- TOC entry 3841 (class 0 OID 33256)
-- Dependencies: 239
-- Data for Name: email_subscriptions; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.email_subscriptions DISABLE TRIGGER ALL;

COPY public.email_subscriptions (id, email, name, is_active, subscription_type, unsubscribe_token, created_at, updated_at) FROM stdin;
6	codeitpy@gmail.com	Adam	t	all	a9c69866-15d0-4d12-9998-449275595f05	2025-08-24 15:10:30.266185	2025-08-24 15:10:30.266227
8	piotr@test.com	Piotr	t	all	e748c5d2-dc86-45e3-b633-8c1ef139794f	2025-08-28 10:31:37.296201	2025-08-28 10:31:37.296207
9	test@example.com	Test User	t	all	addec68e-24aa-43f3-a9c6-4744e1014206	2025-08-28 10:58:35.374058	2025-08-28 14:03:21.866805
11	test2@example.com	Test User 2	t	all	dfd7bd6f-1e7f-4d8f-aa96-0600c175966d	2025-08-28 14:03:34.581288	2025-08-28 14:03:34.581294
12	test3@example.com	Test User 3	t	all	ceaeaff2-e150-4297-ac6c-4fa3cb1f0e6e	2025-08-28 14:05:03.787326	2025-08-28 14:05:03.787338
10	test4@example.com	Test User 4	t	all	0988d064-5387-4f53-8335-749067ba684d	2025-08-28 11:04:16.56598	2025-08-28 15:25:35.638499
13	test6@example.com	Test User 6	t	all	c57f4bb1-6958-40c6-9cf1-74d457fc6e96	2025-08-28 16:22:44.451611	2025-08-28 16:22:44.451628
\.


ALTER TABLE public.email_subscriptions ENABLE TRIGGER ALL;

--
-- TOC entry 3845 (class 0 OID 33287)
-- Dependencies: 243
-- Data for Name: event_schedule; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.event_schedule DISABLE TRIGGER ALL;

COPY public.event_schedule (id, title, event_type, event_date, description, meeting_link, is_active, is_published, created_at, updated_at, end_date, location, calendar_integration, google_calendar_id, outlook_event_id, ical_uid, hero_background, hero_background_type) FROM stdin;
24	TEST - Przypomnienie 5min	Spotkanie	2025-08-29 14:01:02.975363	Wydarzenie testowe - przypomnienie 5min przed. Powinieneś otrzymać email za 5 minut!	\N	f	f	2025-08-29 13:51:02.975363	2025-08-29 13:51:16.868284	2025-08-29 14:31:02.975363	Online - Google Meet	t	\N	\N	\N	\N	image
5	Test Nowe Wydarzenie	Prezentacja	2025-09-04 12:31:22.958958	Testowe wydarzenie do testów	\N	t	t	\N	\N	2025-09-04 14:31:22.958958	\N	t	\N	\N	\N	\N	image
25	TEST - Przypomnienie 1h	Webinar	2025-08-29 15:01:02.975363	Wydarzenie testowe - przypomnienie 1h przed. Powinieneś otrzymać email za 10 minut!	\N	f	f	2025-08-29 13:51:02.975363	2025-09-01 10:24:02.055483	2025-08-29 16:01:02.975363	Online - Teams	t	\N	\N	\N	\N	image
26	TEST - Przypomnienie 2h	Prezentacja	2025-08-29 16:01:02.975363	Wydarzenie testowe - przypomnienie 1h przed. Powinieneś otrzymać email za 1 godzinę i 10 minut!	\N	f	f	2025-08-29 13:51:02.975363	2025-09-01 10:24:02.055492	2025-08-29 18:01:02.975363	Online - Zoom	t	\N	\N	\N	\N	image
\.


ALTER TABLE public.event_schedule ENABLE TRIGGER ALL;

--
-- TOC entry 3865 (class 0 OID 34081)
-- Dependencies: 263
-- Data for Name: event_email_schedules; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.event_email_schedules DISABLE TRIGGER ALL;

COPY public.event_email_schedules (id, event_id, notification_type, status, scheduled_at, sent_at, recipient_group_id, template_id, recipient_count, sent_count, failed_count, created_at, updated_at) FROM stdin;
28	24	5min_before	pending	2025-08-29 13:56:02.975363	\N	9	11	\N	\N	\N	2025-08-29 13:51:07.943917	2025-08-29 13:51:07.943917
29	25	1h_before	pending	2025-08-29 14:01:02.975363	\N	9	10	\N	\N	\N	2025-08-29 13:51:07.943917	2025-08-29 13:51:07.943917
30	25	5min_before	pending	2025-08-29 14:56:02.975363	\N	9	11	\N	\N	\N	2025-08-29 13:51:07.943917	2025-08-29 13:51:07.943917
31	26	1h_before	pending	2025-08-29 15:01:02.975363	\N	9	10	\N	\N	\N	2025-08-29 13:51:07.943917	2025-08-29 13:51:07.943917
32	26	5min_before	pending	2025-08-29 15:56:02.975363	\N	9	11	\N	\N	\N	2025-08-29 13:51:07.943917	2025-08-29 13:51:07.943917
\.


ALTER TABLE public.event_email_schedules ENABLE TRIGGER ALL;

--
-- TOC entry 3849 (class 0 OID 33340)
-- Dependencies: 247
-- Data for Name: event_notifications; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.event_notifications DISABLE TRIGGER ALL;

COPY public.event_notifications (id, event_id, notification_type, status, scheduled_at, sent_at, subject, template_name, recipient_count, created_at, updated_at) FROM stdin;
\.


ALTER TABLE public.event_notifications ENABLE TRIGGER ALL;

--
-- TOC entry 3851 (class 0 OID 33988)
-- Dependencies: 249
-- Data for Name: event_recipient_groups; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.event_recipient_groups DISABLE TRIGGER ALL;

COPY public.event_recipient_groups (id, event_id, name, description, group_type, criteria_config, member_count, is_active, created_at, updated_at) FROM stdin;
\.


ALTER TABLE public.event_recipient_groups ENABLE TRIGGER ALL;

--
-- TOC entry 3847 (class 0 OID 33326)
-- Dependencies: 245
-- Data for Name: event_registrations; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.event_registrations DISABLE TRIGGER ALL;

COPY public.event_registrations (id, event_id, name, email, phone, status, wants_club_news, notification_preferences, created_at, updated_at) FROM stdin;
16	5	xxx	codeitpy@gmail.com		confirmed	t	\N	2025-08-29 08:41:58.912185	2025-08-29 10:52:43.292903
\.


ALTER TABLE public.event_registrations ENABLE TRIGGER ALL;

--
-- TOC entry 3829 (class 0 OID 25095)
-- Dependencies: 227
-- Data for Name: faqs; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.faqs DISABLE TRIGGER ALL;

COPY public.faqs (id, question, answer, "order", is_active, created_at, updated_at) FROM stdin;
3	Co jeśli nie mogę uczestniczyć na żywo?	Zarejestruj się i tak, a wyślemy Ci nagranie (jeśli będzie dostępne).	3	t	2025-08-22 11:37:10.023748	2025-08-22 11:37:10.023752
4	Jak długo trwa prezentacja?	Prezentacja trwa około 60-90 minut, w tym czas na pytania i odpowiedzi.	4	t	2025-08-22 11:37:10.025061	2025-08-22 11:37:10.025067
2	Czy potrzebuję doświadczenia z AI lub rozwojem osobistym?	Nie! Witamy ludzi ze wszystkich środowisk. Prezentacja jest dostosowana do początkujących.	2	t	2025-08-22 11:37:10.022515	2025-08-29 01:03:32.865375
\.


ALTER TABLE public.faqs ENABLE TRIGGER ALL;

--
-- TOC entry 3819 (class 0 OID 25054)
-- Dependencies: 217
-- Data for Name: menu_items; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.menu_items DISABLE TRIGGER ALL;

COPY public.menu_items (id, title, url, "order", is_active, created_at, updated_at) FROM stdin;
2	Korzyści	#benefits	2	t	2025-08-22 11:37:09.936662	2025-08-22 11:37:09.936669
3	O Klubie	#about	3	t	2025-08-22 11:37:09.939271	2025-08-22 11:37:09.939278
5	Zapisz się	#register	5	t	2025-08-22 11:37:09.944601	2025-08-22 11:37:09.944606
1	 Klub „Lepsze życie” 	#hero	1	t	2025-08-22 11:37:09.932531	2025-08-22 11:43:08.11993
\.


ALTER TABLE public.menu_items ENABLE TRIGGER ALL;

--
-- TOC entry 3837 (class 0 OID 33234)
-- Dependencies: 235
-- Data for Name: pages; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.pages DISABLE TRIGGER ALL;

COPY public.pages (id, title, slug, content, meta_description, meta_keywords, is_active, is_published, published_at, created_at, updated_at, "order") FROM stdin;
10	finase	finanse				t	t	2025-08-29 01:06:56.948796	2025-08-29 01:06:56.95179	2025-08-29 01:06:56.951797	0
\.


ALTER TABLE public.pages ENABLE TRIGGER ALL;

--
-- TOC entry 3833 (class 0 OID 25115)
-- Dependencies: 231
-- Data for Name: presentation_schedule; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.presentation_schedule DISABLE TRIGGER ALL;

COPY public.presentation_schedule (id, title, next_presentation_date, custom_text, is_active, created_at, updated_at) FROM stdin;
1	Następna sesja	2025-08-23 10:00:00		t	2025-08-22 11:37:10.036655	2025-08-22 11:37:10.036661
\.


ALTER TABLE public.presentation_schedule ENABLE TRIGGER ALL;

--
-- TOC entry 3827 (class 0 OID 25088)
-- Dependencies: 225
-- Data for Name: registrations; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.registrations DISABLE TRIGGER ALL;

COPY public.registrations (id, name, email, phone, presentation_date, status, created_at, updated_at) FROM stdin;
\.


ALTER TABLE public.registrations ENABLE TRIGGER ALL;

--
-- TOC entry 3831 (class 0 OID 25104)
-- Dependencies: 229
-- Data for Name: seo_settings; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.seo_settings DISABLE TRIGGER ALL;

COPY public.seo_settings (id, page_type, page_title, meta_description, meta_keywords, og_title, og_description, og_image, og_type, twitter_card, twitter_title, twitter_description, twitter_image, canonical_url, structured_data, is_active, created_at, updated_at) FROM stdin;
1	home	Klub Lepsze Życie - Lepsze życie po 50-tce	Dołącz do klubu osób 50+ i odkryj, jak poprawić finanse, zdrowie, budować społeczność i opanować narzędzia AI.	klub 50+, rozwój osobisty, finanse, zdrowie, społeczność, AI, lepsze życie	Klub Lepsze Życie - Lepsze życie po 50-tce	Dołącz do klubu osób 50+ i odkryj, jak poprawić finanse, zdrowie, budować społeczność i opanować narzędzia AI.	static/images/hero/hero-bg.jpg	website	summary_large_image	Klub Lepsze Życie - Lepsze życie po 50-tce	Dołącz do klubu osób 50+ i odkryj, jak poprawić finanse, zdrowie, budować społeczność i opanować narzędzia AI.	static/images/hero/hero-bg.jpg	https://lepszezycie.pl	\N	t	2025-08-24 11:39:29.789113	2025-08-24 11:39:29.789123
\.


ALTER TABLE public.seo_settings ENABLE TRIGGER ALL;

--
-- TOC entry 3825 (class 0 OID 25081)
-- Dependencies: 223
-- Data for Name: social_links; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.social_links DISABLE TRIGGER ALL;

COPY public.social_links (id, platform, url, icon, "order", is_active, created_at) FROM stdin;
2	Instagram	#	fab fa-instagram	2	t	2025-08-22 11:37:10.013559
1	Facebook	#	fab fa-facebook	1	t	2025-08-22 11:37:10.009488
\.


ALTER TABLE public.social_links ENABLE TRIGGER ALL;

--
-- TOC entry 3823 (class 0 OID 25072)
-- Dependencies: 221
-- Data for Name: testimonials; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.testimonials DISABLE TRIGGER ALL;

COPY public.testimonials (id, author_name, content, member_since, rating, is_active, created_at) FROM stdin;
\.


ALTER TABLE public.testimonials ENABLE TRIGGER ALL;

--
-- TOC entry 3861 (class 0 OID 34053)
-- Dependencies: 259
-- Data for Name: user_group_members; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.user_group_members DISABLE TRIGGER ALL;

COPY public.user_group_members (id, group_id, member_type, email, name, member_metadata, is_active, created_at, updated_at) FROM stdin;
1	4	email	codeitpy@gmail.com	Test User	{}	t	2025-08-29 13:41:37.503099	2025-08-29 13:41:37.503099
2	5	email	codeitpy@gmail.com	Test User	{}	t	2025-08-29 13:45:49.62922	2025-08-29 13:45:49.62922
3	6	email	codeitpy@gmail.com	Test User	{}	t	2025-08-29 13:47:34.769834	2025-08-29 13:47:34.769834
4	7	email	codeitpy@gmail.com	Test User	{}	t	2025-08-29 13:48:27.781722	2025-08-29 13:48:27.781722
5	8	email	codeitpy@gmail.com	Test User	{}	t	2025-08-29 13:50:19.092721	2025-08-29 13:50:19.092721
6	9	email	codeitpy@gmail.com	Test User	{}	t	2025-08-29 13:51:07.943917	2025-08-29 13:51:07.943917
\.


ALTER TABLE public.user_group_members ENABLE TRIGGER ALL;

--
-- TOC entry 3817 (class 0 OID 25043)
-- Dependencies: 215
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: shadi
--

ALTER TABLE public.users DISABLE TRIGGER ALL;

COPY public.users (id, username, email, password_hash, is_admin, created_at, last_login, name, is_active, phone, club_member, is_temporary_password) FROM stdin;
1	admin	admin@lepszezycie.pl	scrypt:32768:8:1$i3KseXsr1XZCm2oZ$001907e09aa0716914d6c8083b93c11616488d1485a8ee8ebf891be6b9c620f29b6b280f026e70df8a615cbe4b947128ee0d38c9ab93b89a5a142eeed2d5d583	t	2025-08-22 11:37:09.901794	\N	admin	t	\N	f	f
15	\N	codeitpy@gmail.com	scrypt:32768:8:1$M03csXUCcq92JnIt$118a4f73a0dfd1a5e626731a116a9e086cfc5f9626953186c2320e11a998d46089ad0dc919997405240f4a73456090397a50b644bcb667317a17d2c0c0012927	f	2025-08-29 08:41:56.407291	2025-08-29 08:49:28.440453	xxx	t		t	f
\.


ALTER TABLE public.users ENABLE TRIGGER ALL;

--
-- TOC entry 3871 (class 0 OID 0)
-- Dependencies: 232
-- Name: benefit_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.benefit_items_id_seq', 8, true);


--
-- TOC entry 3872 (class 0 OID 0)
-- Dependencies: 260
-- Name: email_automation_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.email_automation_logs_id_seq', 1, false);


--
-- TOC entry 3873 (class 0 OID 0)
-- Dependencies: 254
-- Name: email_automations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.email_automations_id_seq', 8, true);


--
-- TOC entry 3874 (class 0 OID 0)
-- Dependencies: 252
-- Name: email_campaigns_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.email_campaigns_id_seq', 1, false);


--
-- TOC entry 3875 (class 0 OID 0)
-- Dependencies: 240
-- Name: email_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.email_logs_id_seq', 17, true);


--
-- TOC entry 3876 (class 0 OID 0)
-- Dependencies: 256
-- Name: email_schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.email_schedules_id_seq', 5, true);


--
-- TOC entry 3877 (class 0 OID 0)
-- Dependencies: 238
-- Name: email_subscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.email_subscriptions_id_seq', 13, true);


--
-- TOC entry 3878 (class 0 OID 0)
-- Dependencies: 236
-- Name: email_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.email_templates_id_seq', 23, true);


--
-- TOC entry 3879 (class 0 OID 0)
-- Dependencies: 262
-- Name: event_email_schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.event_email_schedules_id_seq', 32, true);


--
-- TOC entry 3880 (class 0 OID 0)
-- Dependencies: 246
-- Name: event_notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.event_notifications_id_seq', 1, false);


--
-- TOC entry 3881 (class 0 OID 0)
-- Dependencies: 248
-- Name: event_recipient_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.event_recipient_groups_id_seq', 1, false);


--
-- TOC entry 3882 (class 0 OID 0)
-- Dependencies: 244
-- Name: event_registrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.event_registrations_id_seq', 16, true);


--
-- TOC entry 3883 (class 0 OID 0)
-- Dependencies: 242
-- Name: event_schedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.event_schedule_id_seq', 26, true);


--
-- TOC entry 3884 (class 0 OID 0)
-- Dependencies: 226
-- Name: faqs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.faqs_id_seq', 6, true);


--
-- TOC entry 3885 (class 0 OID 0)
-- Dependencies: 216
-- Name: menu_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.menu_items_id_seq', 6, true);


--
-- TOC entry 3886 (class 0 OID 0)
-- Dependencies: 234
-- Name: pages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.pages_id_seq', 10, true);


--
-- TOC entry 3887 (class 0 OID 0)
-- Dependencies: 230
-- Name: presentation_schedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.presentation_schedule_id_seq', 1, true);


--
-- TOC entry 3888 (class 0 OID 0)
-- Dependencies: 224
-- Name: registrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.registrations_id_seq', 8, true);


--
-- TOC entry 3889 (class 0 OID 0)
-- Dependencies: 218
-- Name: sections_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.sections_id_seq', 9, true);


--
-- TOC entry 3890 (class 0 OID 0)
-- Dependencies: 228
-- Name: seo_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.seo_settings_id_seq', 1, true);


--
-- TOC entry 3891 (class 0 OID 0)
-- Dependencies: 222
-- Name: social_links_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.social_links_id_seq', 5, true);


--
-- TOC entry 3892 (class 0 OID 0)
-- Dependencies: 220
-- Name: testimonials_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.testimonials_id_seq', 11, true);


--
-- TOC entry 3893 (class 0 OID 0)
-- Dependencies: 258
-- Name: user_group_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.user_group_members_id_seq', 6, true);


--
-- TOC entry 3894 (class 0 OID 0)
-- Dependencies: 250
-- Name: user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.user_groups_id_seq', 9, true);


--
-- TOC entry 3895 (class 0 OID 0)
-- Dependencies: 214
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shadi
--

SELECT pg_catalog.setval('public.users_id_seq', 15, true);


-- Completed on 2025-09-01 14:17:47 CEST

--
-- PostgreSQL database dump complete
--

\unrestrict ceVgrd761HiXI806R51VUrzpYe0tQXMWNZ9wQBCcmae6VnHylwAJYaFnj03q4xj

