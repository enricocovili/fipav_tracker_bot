from telethon import events, Button
import logging
import handlers.base_handler as base_handler
import db.crud
from db.user_state import UserState
from standing_manager import StandingManager
from team_info_manager import TeamInfoManager
from db.models import Championship


class MainMenu(base_handler.BaseHandler):
    back_to_menu_button = Button.inline("Torna al menu", b"_menu")
    back_to_championship_button = Button.inline("Torna")
    back_to_start_button = Button.inline("Torna al menu principale", b"_menu_start")
    explore_button = Button.inline("🏆 Esplora i campionati", b"_menu_explore")
    profile_button = Button.inline("👤 Il mio profilo", b"_menu_profile")

    async def send_standings(
        event: events.newmessage.NewMessage.Event, is_avulsa: bool
    ):
        logging.info(
            f"received: ranking: {'avulsa' if is_avulsa else 'girone'}")
        user_state: UserState = event.client.users_state[event.chat_id]
        loading_msg = await event.edit("Loading...")
        try:
            standing_manager = StandingManager(
                championship=user_state.championship_selected, is_avulsa=is_avulsa
            )
            png = standing_manager.create_image(
                {t.id for t in db.crud.get_user_teams(event.chat_id)}
            )
        except Exception as e:
            logging.error(e)
            await event.edit(f"Error while processing: {e}")
            return
        await loading_msg.delete()
        await event.client.send_file(
            event.chat,
            StandingManager.as_file(png),
            caption=f"Classifica\nPartite: {standing_manager.championship.url}",
        )

    async def team_selection(
        event: events.newmessage.NewMessage.Event,
        campionato: Championship,
        event_type: str,
    ):
        teams = db.crud.get_teams_by_championship(campionato.id)
        tracked_ids = (
            {t.id for t in db.crud.get_user_teams(event.chat_id)}
            if event_type == "notification"
            else set()
        )
        buttons = [
            [
                Button.inline(
                    f"{'🔔 ' if team.id in tracked_ids else ''}{team.name}",
                    f"_team_choice_{team.id}_{event_type}")
                for team in teams[i: i + 1]
            ]
            for i in range(0, len(teams))
        ]
        buttons.append([Button.inline("Torna al menu", data=b"_menu")])
        await event.edit(
            "Seleziona squadra"
            + (" (tocca per attivare/disattivare le notifiche)" if event_type == "notification" else ""),
            buttons=buttons,
        )

    def ensure_user(event: events.newmessage.NewMessage.Event):
        if not db.crud.get_user(user_id=event.chat_id):
            db.crud.create_user(id=event.chat_id, username=event.chat.username)
            logging.info(f"Created User {event.chat.username}")

    async def user_choice(event: events.newmessage.NewMessage.Event):
        championship = event.client.users_state[event.chat_id].championship_selected
        tracking = db.crud.is_tracking_championship(event.chat_id, championship.id)
        await event.edit(
            f"SELEZIONE:{championship.name}\nCosa vuoi fare?",
            buttons=[
                [
                    Button.inline(
                        "🔔 Abilita notifiche per squadra singola",
                        b"_menu_enable_team_notification",
                    )
                ],
                [
                    Button.inline(
                        "🔕 Disabilita notifiche per campionato"
                        if tracking
                        else "🔔 Abilita notifiche per campionato",
                        b"_menu_toggle_championship_notification",
                    )
                ],
                [
                    Button.inline(
                        "🔍 Informazioni su una squadra",
                        b"_menu_get_team_info",
                    )
                ],
                [
                    Button.inline(
                        "🥇 Classifica",
                        b"_menu_campionship_rankings",
                    )
                ],
                [Button.inline("Torna alla scelta girone",
                               f"_championship_{championship.id}".encode())],
            ],
        )

    @events.register(events.CallbackQuery)
    async def callback(event: events.newmessage.NewMessage.Event):
        data: str = event.data.decode()
        user_state = event.client.users_state.setdefault(
            event.chat_id, UserState())

        if data.startswith("_championship_choice_"):
            user_state.championship_selected = db.crud.get_championship_by_id(
                data.split("_")[-1]
            )
            await MainMenu.user_choice(event)
            return

        if data.startswith("_championship_"):
            await MainMenu.group_selection(
                event, db.crud.get_championship_by_id(data.split("_")[-1])
            )
            return

        campionato = user_state.championship_selected

        if data.startswith("_team_choice_"):
            team_id = int(data.split("_")[-2])
            team = db.crud.get_team_by_id(team_id=team_id)
            if data.endswith("_notification"):
                event.client.users_state[event.chat_id].team_selected = team
                MainMenu.ensure_user(event)
                if db.crud.is_tracking_team(event.chat_id, team_id):
                    db.crud.untrack_team(event.chat_id, team_id)
                    logging.info(
                        f"User {event.chat.username} stopped tracking {team.name}")
                    text = f"🔕 Notifiche disabilitate per {team.name}"
                else:
                    db.crud.track_team(event.chat_id, team_id)
                    logging.info(
                        f"User {event.chat.username} started tracking {team.name}")
                    text = f"✅ Notifiche abilitate per {team.name}"
                await event.edit(text, buttons=[MainMenu.back_to_menu_button])
            elif data.endswith("_info"):
                await event.edit(
                    TeamInfoManager.team_stats(team, campionato),
                    buttons=[MainMenu.back_to_menu_button],
                )

            return

        match event.data:
            case b"_menu_start":
                await MainMenu.handle(event)
            case b"_menu_explore":
                await MainMenu.championship_selection(event)
            case b"_menu_profile":
                await MainMenu.show_profile(event)
            case b"_menu":
                await MainMenu.user_choice(event)
            case b"_menu_enable_team_notification":
                await MainMenu.team_selection(event, campionato, "notification")
            case b"_menu_toggle_championship_notification":
                MainMenu.ensure_user(event)
                if db.crud.is_tracking_championship(event.chat_id, campionato.id):
                    db.crud.untrack_championship(event.chat_id, campionato.id)
                    logging.info(
                        f"{event.chat.username} stopped tracking championship {campionato.name} - {campionato.group_name}"
                    )
                    text = "🔕 Notifiche per il campionato disabilitate."
                else:
                    db.crud.track_championship(event.chat_id, campionato.id)
                    logging.info(
                        f"{event.chat.username} started tracking championship {campionato.name} - {campionato.group_name}"
                    )
                    text = "✅ Notifiche per il campionato abilitate! Riceverai aggiornamenti sulle partite."
                await event.edit(text, buttons=[MainMenu.back_to_menu_button])

            case b"_menu_get_team_info":
                await MainMenu.team_selection(event, campionato, "info")

            case b"_menu_campionship_rankings":
                await event.edit(
                    "Quale classifica vuoi vedere?",
                    buttons=[
                        [
                            Button.inline("Girone", b"_menu_ranking_girone"),
                            Button.inline("Avulsa", b"_menu_ranking_avulsa"),
                        ],
                        [
                            MainMenu.back_to_menu_button,
                        ],
                    ],
                )

            case b"_menu_ranking_girone":
                await MainMenu.send_standings(event, is_avulsa=False)

            case b"_menu_ranking_avulsa":
                await MainMenu.send_standings(event, is_avulsa=True)

            case _:
                await event.edit("Comando non riconosciuto.")

    @staticmethod
    async def reply(event, text: str, buttons) -> None:
        """Edit the message when coming from a button, else send a new one."""
        if hasattr(event.original_update, "data"):
            await event.edit(text, buttons=buttons)
        else:
            await event.client.send_message(
                event.chat, message=text, buttons=buttons)

    async def championship_selection(event: events.newmessage.NewMessage.Event):
        """Whole championships (all their groups merged under one name)."""
        tracked_ids = {
            c.id for c in db.crud.get_user_championships(event.chat_id)}
        groups_by_name: dict[str, list[Championship]] = {}
        for championship in db.crud.get_all_championships():
            groups_by_name.setdefault(championship.name, []).append(championship)
        buttons = [
            [
                Button.inline(
                    f"{'🔔 ' if tracked_ids & {g.id for g in groups} else ''}{name}",
                    f"_championship_{groups[0].id}".encode(),
                )
            ]
            for name, groups in groups_by_name.items()
        ]
        buttons.append([MainMenu.back_to_start_button])
        await MainMenu.reply(event, "Scegli un campionato:", buttons)

    async def group_selection(
        event: events.newmessage.NewMessage.Event, championship: Championship
    ):
        tracked_ids = {
            c.id for c in db.crud.get_user_championships(event.chat_id)}
        groups = db.crud.get_championships_by_name(championship.name)
        buttons = [
            [
                Button.inline(
                    f"{'🔔 ' if group.id in tracked_ids else ''}Girone {group.group_name}",
                    f"_championship_choice_{group.id}".encode(),
                )
            ]
            for group in sorted(groups, key=lambda g: g.group_name or "")
        ]
        buttons.append(
            [Button.inline("Torna alla scelta campionato", b"_menu_explore")])
        await event.edit(
            f"**{championship.name}**\nScegli un girone:", buttons=buttons)

    async def show_profile(event: events.newmessage.NewMessage.Event):
        championships = db.crud.get_user_championships(event.chat_id)
        teams = db.crud.get_user_teams(event.chat_id)
        championships_text = "\n".join(
            f"• {c.name} - Girone {c.group_name}" for c in championships
        ) or "nessuno"
        teams_text = "\n".join(
            f"• {t.name}" for t in teams) or "nessuna"
        await MainMenu.reply(
            event,
            f"**Il tuo profilo**\n\n"
            f"**Campionati tracciati**\n{championships_text}\n\n"
            f"**Squadre tracciate**\n{teams_text}",
            [
                [MainMenu.explore_button],
                [MainMenu.back_to_start_button],
            ],
        )

    @events.register(events.NewMessage(pattern="/profile"))
    async def profile(event: events.newmessage.NewMessage):
        await MainMenu.show_profile(event)

    @events.register(events.NewMessage(pattern="/start"))
    async def handle(event: events.newmessage.NewMessage):
        event.client.users_state[event.chat_id] = UserState()
        await MainMenu.reply(
            event,
            "**Tracciamento partite per FIPAV Modena**",
            [[MainMenu.explore_button], [MainMenu.profile_button]],
        )
