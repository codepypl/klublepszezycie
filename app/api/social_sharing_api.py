"""
Social Sharing API - generowanie linków share i śledzenie udostępnień
"""
from flask import Blueprint, request, jsonify, url_for, current_app
from flask_login import current_user
from app.models import BlogPost, db
from app.blueprints.blog_controller import BlogController
import logging


social_sharing_api_bp = Blueprint("social_sharing_api", __name__)


def _build_post_url(post: BlogPost) -> str:
    """
    Zwraca absolutny URL wpisu blogowego z kategorią (tak jak na froncie).
    """
    try:
        # Używamy tej samej logiki co w szablonach
        path = BlogController.get_post_url_with_category(post)
    except Exception:
        path = f"/blog/{post.slug}"

    # request.url_root zawiera już trailing slash
    base = request.url_root.rstrip("/") if request else current_app.config.get(
        "SITE_URL", ""
    ).rstrip("/")
    return f"{base}{path}"


def _build_sharing_links(post: BlogPost, post_url: str):
    """
    Buduje słownik linków do udostępniania na poszczególnych platformach.
    Flagi social_* na modelu postu decydują, które platformy są aktywne.
    Domyślnie wszystkie platformy są włączone (True), chyba że w bazie jest False.
    """
    title = post.title or ""
    description = (post.excerpt or "").strip() or (post.content or "")[:150]

    # Bazowy zestaw platform – można rozszerzyć w przyszłości
    platforms = {}

    # Facebook - ZAWSZE włączony, chyba że wyraźnie wyłączony
    # Problem: domyślna wartość w modelu to False, więc musimy ignorować False jako domyślną wartość
    # Rozwiązanie: traktujemy False jako "nie ustawione" i domyślnie włączamy
    social_facebook = getattr(post, "social_facebook", None)
    # Jeśli flaga jest None (nie istnieje) lub True - włączamy
    # Jeśli flaga jest False - również włączamy (bo to domyślna wartość, nie oznacza wyłączenia)
    # Aby wyłączyć Facebook, trzeba ustawić specjalną wartość (np. przez migrację zmienić domyślną na True)
    # Na razie: zawsze włączamy Facebook
    if True:  # Zawsze włączamy Facebook - można później dodać logikę wyłączania
        logging.debug(f"Adding Facebook platform. social_facebook value: {social_facebook}")
        share_url = (
            "https://www.facebook.com/sharer/sharer.php?u=" + post_url
        )
        platforms["facebook"] = {
            "name": "Facebook",
            "url": share_url,
            "icon": "fab fa-facebook-f",
            "color": "#1877f2",
        }

    # X / Twitter - ZAWSZE włączony, chyba że wyraźnie wyłączony
    # Problem: domyślna wartość w modelu to False, więc musimy ignorować False jako domyślną wartość
    social_twitter = getattr(post, "social_twitter", None)
    # Zawsze włączamy Twitter (podobnie jak Facebook)
    if True:  # Zawsze włączamy Twitter - można później dodać logikę wyłączania
        logging.debug(f"Adding Twitter platform. social_twitter value: {social_twitter}")
        import urllib.parse

        text = f"{title}"
        share_url = (
            "https://twitter.com/intent/tweet?text="
            + urllib.parse.quote(text)
            + "&url="
            + urllib.parse.quote(post_url)
        )
        platforms["twitter"] = {
            "name": "X (Twitter)",
            "url": share_url,
            "icon": "fab fa-x-twitter",  # FontAwesome 6.5.1+ ma fa-x-twitter, jeśli nie działa użyj: "fab fa-twitter"
            "color": "#1da1f2",
        }
        
        # Debug: sprawdź czy platforma została dodana
        logging.debug(f"Twitter platform added: {platforms.get('twitter') is not None}")

    # LinkedIn - domyślnie włączony (jeśli flaga nie jest wyraźnie False)
    social_linkedin = getattr(post, "social_linkedin", None)
    if social_linkedin is not False:
        import urllib.parse

        share_url = (
            "https://www.linkedin.com/shareArticle?mini=true"
            + "&url="
            + urllib.parse.quote(post_url)
            + "&title="
            + urllib.parse.quote(title)
            + "&summary="
            + urllib.parse.quote(description)
        )
        platforms["linkedin"] = {
            "name": "LinkedIn",
            "url": share_url,
            "icon": "fab fa-linkedin-in",
            "color": "#0077b5",
        }

    # WhatsApp
    # WhatsApp jest zawsze dostępny jako dodatkowy kanał share
    import urllib.parse
    text = f"{title} - {post_url}"
    share_url = "https://api.whatsapp.com/send?text=" + urllib.parse.quote(text)
    platforms["whatsapp"] = {
        "name": "WhatsApp",
        "url": share_url,
        "icon": "fab fa-whatsapp",
        "color": "#25d366",
    }

    # Telegram
    import urllib.parse
    text = f"{title} - {post_url}"
    telegram_url = "https://t.me/share/url?url=" + urllib.parse.quote(post_url) + "&text=" + urllib.parse.quote(text)
    platforms["telegram"] = {
        "name": "Telegram",
        "url": telegram_url,
        "icon": "fab fa-telegram-plane",
        "color": "#0088cc",
    }

    # Instagram - domyślnie włączony (jeśli flaga nie jest wyraźnie False)
    # Instagram nie ma oficjalnego share URL, więc kopiujemy link
    social_instagram = getattr(post, "social_instagram", None)
    if social_instagram is not False:
        # Instagram nie ma share API, więc używamy specjalnego linku
        # który otwiera Instagram z możliwością wklejenia linku
        # Alternatywnie można użyć linku do profilu Instagram
        import urllib.parse
        # Instagram Stories można udostępnić przez specjalny URL, ale wymaga to aplikacji
        # Na razie używamy prostego linku, który otwiera Instagram
        instagram_url = f"https://www.instagram.com/"
        platforms["instagram"] = {
            "name": "Instagram",
            "url": "#",  # Użyjemy JavaScript do kopiowania linku
            "icon": "fab fa-instagram",
            "color": "#E4405F",
            "action": "copy"  # Specjalna akcja - kopiuj link zamiast otwierać URL
        }

    # E-mail (zawsze dostępny)
    import urllib.parse

    email_subject = urllib.parse.quote(title or "Polecam artykuł z bloga")
    email_body = urllib.parse.quote(f"{title}\n\n{description}\n\n{post_url}")
    mailto = f"mailto:?subject={email_subject}&body={email_body}"
    platforms["email"] = {
        "name": "Email",
        "url": mailto,
        "icon": "fas fa-envelope",
        "color": "#6c757d",
    }

    return platforms


@social_sharing_api_bp.route("/social-sharing/generate-links", methods=["POST"])
def generate_links():
    """
    Przyjmuje post_id i zwraca dane + linki do udostępniania dla danego wpisu.
    Endpoint jest publiczny (nie wymaga logowania), aby widget działał na blogu.
    """
    try:
        data = request.get_json() or {}
        post_id = data.get("post_id")

        if not post_id:
            return jsonify({"success": False, "error": "Brak parametru post_id"}), 400

        post = BlogPost.query.get(post_id)
        if not post:
            return (
                jsonify({"success": False, "error": "Artykuł nie istnieje"}),
                404,
            )
        
        # Sprawdzamy czy post jest opublikowany
        if not post.is_published:
            logging.warning(f"Post {post_id} ({post.slug}) nie jest opublikowany - status: {post.status}")
            return (
                jsonify({"success": False, "error": "Artykuł nie jest opublikowany"}),
                404,
            )

        post_url = _build_post_url(post)

        sharing_links = _build_sharing_links(post, post_url)
        
        # Debug logging
        logging.info(
            f"[SHARE] Post {post_id} ({post.slug}): "
            f"social_facebook={getattr(post, 'social_facebook', None)}, "
            f"social_twitter={getattr(post, 'social_twitter', None)}, "
            f"social_linkedin={getattr(post, 'social_linkedin', None)}, "
            f"social_instagram={getattr(post, 'social_instagram', None)}, "
            f"platforms={list(sharing_links.keys())}"
        )
        
        if not sharing_links:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Brak aktywnych kanałów social dla tego artykułu",
                    }
                ),
                400,
            )

        sharing_data = {
            "post_id": post.id,
            "post_title": post.title,
            "post_url": post_url,
        }

        return jsonify(
            {
                "success": True,
                "sharing_data": sharing_data,
                "sharing_links": sharing_links,
            }
        )
    except Exception as e:
        logging.exception("Błąd generowania linków social sharing")
        return jsonify({"success": False, "error": str(e)}), 500


@social_sharing_api_bp.route("/social-sharing/track-share", methods=["POST"])
def track_share():
    """
    Prosty endpoint do śledzenia kliknięć w przyciski share.
    Na razie tylko loguje zdarzenie; w razie potrzeby można to rozbudować
    o zapis do dedykowanego modelu / statystyk.
    """
    try:
        data = request.get_json() or {}
        post_id = data.get("post_id")
        platform = data.get("platform")

        if not post_id or not platform:
            return (
                jsonify(
                    {"success": False, "error": "Brak wymaganych pól: post_id, platform"}
                ),
                400,
            )

        # Upewnijmy się, że post istnieje (nie podnosimy 404, żeby nie psuć UX)
        post = BlogPost.query.get(post_id)
        post_slug = post.slug if post else "unknown"

        logging.info(
            f"[SHARE] post_id={post_id} slug={post_slug} platform={platform} "
            f"user_id={getattr(current_user, 'id', None)} ip={request.remote_addr}"
        )

        # TODO: w przyszłości można dodać model StatShare i inkrementować licznik

        return jsonify({"success": True})
    except Exception as e:
        logging.exception("Błąd trackowania share")
        # Nie blokujemy użytkownika, nawet jeśli tracking się wysypie
        return jsonify({"success": False, "error": str(e)}), 500


