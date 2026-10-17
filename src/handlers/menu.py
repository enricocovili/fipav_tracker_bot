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
            filename = standing_manager.create_table(image=True)
        except Exception as e:
            logging.error(e)
            await event.edit(f"Error while processing: {e}")
            return
        await loading_msg.delete()
        await event.client.send_file(
            event.chat,
            filename,
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
                [Button.inline("Torna alla scelta campionato",
                               b"_menu_start")],
            ],
        )

    @events.register(events.CallbackQuery)
    async def callback(event: events.newmessage.NewMessage.Event):
        data: str = event.data.decode()

        if data.startswith("_championship_choice_"):
            event.client.users_state[
                event.chat_id
            ].championship_selected = db.crud.get_championship_by_id(
                data.split("_")[-1]
            )
            await MainMenu.user_choice(event)
            return

        campionato = event.client.users_state[event.chat_id].championship_selected

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

    @events.register(events.NewMessage(pattern="/start"))
    async def handle(event: events.newmessage.NewMessage):
        bot = event.client
        # retrieve championships from db
        championships = db.crud.get_all_championships()
        bot.users_state[event.chat_id] = UserState()
        message_text = (
            "Attualmente solo FIPAV Modena è supportata.\nScegli un campionato:"
        )
        tracked_ids = {
            c.id for c in db.crud.get_user_championships(event.chat_id)}
        buttons = [
            [
                Button.inline(
                    f"{'🔔 ' if championship.id in tracked_ids else ''}"
                    f"{championship.name} - {championship.group_name}",
                    f"_championship_choice_{championship.id}".encode(),
                )
            ]
            for championship in championships
        ]
        if hasattr(event.original_update, "data"):  # back to menu from a submenu
            await event.edit(message_text, buttons=buttons)
        else:  # plain new message (sent by a command)
            await bot.send_message(
                event.chat,
                message=message_text,
                buttons=buttons,
            )
