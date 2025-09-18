from telethon import events, Button
import logging
import handlers.base_handler as base_handler
import db.crud
from db.user_state import UserState
from standing_manager import StandingManager


class MainMenu(base_handler.BaseHandler):
    async def send_standings(
        event: events.newmessage.NewMessage.Event, is_avulsa: bool
    ):
        logging.info(f"received: ranking: {'avulsa' if is_avulsa else 'girone'}")
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
            caption="Classifica",
        )

    async def user_choice(event: events.newmessage.NewMessage.Event):
        await event.edit(
            f"SELEZIONE:{event.client.users_state[event.chat_id].championship_selected.name}\nCosa vuoi fare?",
            buttons=[
                [
                    Button.inline(
                        "🔔 Abilita notifiche per squadra singola",
                        b"_menu_enable_single_notification",
                    )
                ],
                [
                    Button.inline(
                        "🔔 Abilita notifiche per campionato",
                        b"_menu_enable_championship_notification",
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
            ],
        )

    @events.register(events.CallbackQuery)
    async def callback(event: events.newmessage.NewMessage.Event):
        if event.data.decode().startswith("_championship_choice_"):
            event.client.users_state[
                event.chat_id
            ].championship_selected = db.crud.get_championship_by_id(
                event.data.decode().split("_")[-1]
            )
            await MainMenu.user_choice(event)
            return

        if event.data.decode().startswith("_team_choice_"):
            team_id = event.data.decode().split("_")[-1]
            team = db.crud.get_team_by_id(team_id=team_id)
            event.client.users_state[event.chat_id].team_selected = team
            db.crud.update_user(user_id=event.chat_id, **{"tracked_team": team_id})
            logging.info(
                f"User {db.crud.get_user(user_id=event.chat_id).username} started tracking {team.name}"
            )
            await event.edit(f"✅ Notifiche abilitate per {team.name}")
            return

        campionato = event.client.users_state[event.chat_id].championship_selected
        match event.data:
            case b"_menu_enable_single_notification":
                teams = db.crud.get_teams_by_championship(campionato.id)
                buttons = [
                    [
                        Button.inline(team.name, f"_team_choice_{team.id}")
                        for team in teams[i : i + 1]
                    ]
                    for i in range(0, len(teams))
                ]
                await event.edit("Seleziona squadra", buttons=buttons)

            case b"_menu_enable_championship_notification":
                if event.chat.username not in [u.username for u in db.crud.get_users()]:
                    db.crud.create_user(id=event.chat_id, username=event.chat.username)
                    logging.info(
                        f"Created User {event.chat.username} and registered for {campionato.name}"
                    )
                db.crud.update_user(
                    event.chat_id, **{"tracked_championship": campionato.id}
                )
                logging.info(
                    f"Updated {event.chat.username} to track championship {campionato.name}"
                )
                await event.edit(
                    "✅ Notifiche per il campionato abilitate! Riceverai aggiornamenti sulle partite."
                )

            case b"_menu_get_team_info":
                info = MainMenu.team_stats(event)
                await event.edit(info)

            case b"_menu_campionship_rankings":
                await event.edit(
                    "Quale classifica vuoi vedere?",
                    buttons=[
                        [
                            Button.inline("Girone", b"_menu_ranking_girone"),
                            Button.inline("Avulsa", b"_menu_ranking_avulsa"),
                        ]
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
        await bot.send_message(
            event.chat,
            message="Attualmente solo FIPAV Modena è supportata.\nScegli un campionato:",
            buttons=[
                [
                    Button.inline(
                        f"{championship.name} - {championship.group_name}",
                        f"_championship_choice_{championship.id}".encode(),
                    )
                ]
                for championship in championships
            ],
        )
