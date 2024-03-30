import streamlit as st
import sqlite3
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import time
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import pandas.io.sql as psql



# Connect to SQLite database
conn = sqlite3.connect('giro_d_italia.db')

# Create tables if they don't exist
conn.execute('''
    CREATE TABLE IF NOT EXISTS riders_team (
        name TEXT,
        url TEXT,
        team TEXT,
        id INTEGER PRIMARY KEY
    )
''')
# Create tables if they don't exist
conn.execute('''
    CREATE TABLE IF NOT EXISTS teams_finale (
        id INTEGER PRIMARY KEY,
        stage INT,
        position INT,
        rider TEXT,
        team TEXT
    )
''')

# Create tables if they don't exist
conn.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY,
        stage INT,
        position INT,
        rider TEXT,
        team TEXT
    )
''')

conn.execute('''
    CREATE TABLE IF NOT EXISTS ranking (
        id INTEGER PRIMARY KEY,
        rider_id INTEGER,
        stage INTEGER,
        time TEXT,
        FOREIGN KEY(rider_id) REFERENCES riders(id)
    )
''')

conn.execute('''
    CREATE TABLE IF NOT EXISTS iscritti (
        id INTEGER PRIMARY KEY,
        user TEXT,
        team TEXT
    )
''')

with open(r'C:\Users\it-pc-BHF8CK3\Downloads\fantagiro\venv\credentials.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

cursor = conn.cursor()

# Commit the changes to the database
conn.commit()


def vedi_giocate(tappa):
    dfs = read_giocate_giornata(tappa)
    dfs = dfs.set_index(0)
    dfs.columns = ["Tappa", "Posizione", "Corridore", "Squadra"]
    n_squadre = len(dfs.Squadra.unique())
    col1, col2 = st.columns(2)
    pos = "dummy_1"
    point = "dummy_2"
    for i in range(n_squadre):
        sq = list(dfs.Squadra.unique())[i]
        if i % 2 == 0:
            col1.write(f"Squadra: {sq} - {pos} - {point}")
            col1.dataframe(dfs.loc[dfs.Squadra == sq])
        else:
            col2.write(f"Squadra: {sq} - {pos} - {point}")
            col2.dataframe(dfs.loc[dfs.Squadra == sq])
    return


def add_rider(rider, posizione, tappa, squadra):
    query = "INSERT INTO teams (stage, position, rider, team) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (tappa, posizione, rider, squadra))
    # Commit the changes to the database
    conn.commit()
    return


def read_giocate_giornata(tappa):
    query = f"SELECT * FROM teams WHERE stage = {tappa}"
    res = cursor.execute(query)
    df = pd.DataFrame(res.fetchall())
    return df


def read_giocata_giornata(tappa, squadra):
    if tappa == "finale":
        query = f"SELECT * FROM teams_finale WHERE team = '{squadra}'"
    else:
        query = f"SELECT * FROM teams WHERE stage = {tappa} AND team = '{squadra}'"
    res = cursor.execute(query)
    df = pd.DataFrame(res.fetchall())
    return df


def delete_giocata_giornata(tappa, squadra):
    if tappa == "finale":
        query = f"DELETE FROM teams_final WHERE team = '{squadra}'"
    else:
        query = f"DELETE FROM teams WHERE stage = {tappa} AND team = '{squadra}'"
    res = cursor.execute(query)
    df = pd.DataFrame(res.fetchall())
    conn.commit()
    return df


def create_team_page(tappa, squadra):
    st.sidebar.title(f"Crea la tua squadra di giornata per la tappa {tappa}")
    st.title("La tua squadra")
    df = read_giocata_giornata(tappa, squadra)
    position_available = ["1 di giornata", "2 di giornata", "3 di giornata", "Maglia rosa", "2 generale",
                          "3 generale"]
    if df.empty:
        st.write("Non hai giocato nessuno")
    elif df.shape[0] == 6:
        st.write("Hai completato la tua giocata")
        df = df.set_index(0)
        df.columns = ["Tappa", "Posizione", "Corridore", "Squadra"]
        # Define the cell editor parameters
        cell_editor_params = {
            'values': position_available
        }

        # Create a GridOptionsBuilder
        gb = GridOptionsBuilder.from_dataframe(df)

        # Configure the columns
        gb.configure_column('Posizione', cellEditor='agSelectCellEditor', cellEditorParams=cell_editor_params,
                            editable=True)
        gb.configure_column('Corridore', editable=False)
        gb.configure_column('Squadra', editable=False)
        gb.configure_column('Tappa', editable=False)
        # Build the grid options
        gridOptions = gb.build()
        # Display the DataFrame with AgGrid
        grid_return = AgGrid(df, gridOptions=gridOptions, editable=True, enable_delete=True)
        # Get the updated DataFrame
        updated_df = grid_return['data']
        # st.data_editor(updated_df)
        time.sleep(6)
        return
    else:
        st.write("La tua giocata per ora:")
        df = df.set_index(0)
        df.columns = ["Tappa", "Posizione", "Corridore", "Squadra"]
        # Define the cell editor parameters
        cell_editor_params = {
            'values': position_available
        }

        # Create a GridOptionsBuilder
        gb = GridOptionsBuilder.from_dataframe(df)

        # Configure the columns
        gb.configure_column('Posizione', cellEditor='agSelectCellEditor', cellEditorParams=cell_editor_params,
                            editable=True)
        gb.configure_column('Corridore', editable=False)
        gb.configure_column('Squadra', editable=False)
        gb.configure_column('Tappa', editable=False)
        # Build the grid options
        gridOptions = gb.build()
        # Display the DataFrame with AgGrid
        grid_return = AgGrid(df, gridOptions=gridOptions, editable=True, enable_delete=True)
        # Get the updated DataFrame
        updated_df = grid_return['data']
        # st.data_editor(updated_df)
    if st.button("Cancella tutte le tue giocate di giornata"):
        delete_giocata_giornata(tappa, squadra)
        st.write("Giocate cancellate")
        st.rerun()
    # Search bar for rider name
    rider_name = st.sidebar.text_input("Trova corridore:")
    st.write(rider_name)
    selected_rider = None
    total_rider = pd.read_csv(r"C:\Users\it-pc-BHF8CK3\Downloads\fantagiro\venv\riders_df.csv").drop_duplicates("riders")
    total_rider["riders"] = total_rider["riders"].str.replace("-", " ")
    # Filter by team (you can customize this based on your data)
    team_filter = st.sidebar.selectbox("Filtra per squadra", ["All Teams"] + list(total_rider.team.unique()))
    # Display rider stats
    if rider_name:
        filtered_riders = [r for n, r in total_rider.iterrows() if rider_name.lower() in r.riders.lower()]
        if team_filter != "All Teams":
            filtered_riders = [r for r in filtered_riders if r["team"] == team_filter]
        if filtered_riders:
            selected_rider = st.sidebar.selectbox("Select a rider:", [r["riders"] for r in filtered_riders])
            #rider_stats = next((r["stats"] for r in filtered_riders if r["name"] == selected_rider), "")
            #st.write(f"Stats for {selected_rider}:\n{rider_stats}")
        else:
            st.warning("No matching riders found.")
    # Position selection
    if selected_rider:

        if not df.empty:
            position_available = [p for p in position_available if p not in list(df.Posizione.unique())]
        position = st.selectbox("Scegli posizione:", position_available)
        st.write(f"{position} - {selected_rider}")
        if position:
            if st.button("Enter rider"):
                add_rider(selected_rider, position, tappa, squadra)
                st.write(f"{selected_rider} aggiunto in posizione {position}")
                st.rerun()
    return


def create_team_page_final(squadra):
    st.sidebar.title(f"Crea la tua squadra di giornata per la classifica finale")
    st.title("La tua squadra")
    df = read_giocata_giornata("finale", squadra)
    position_available = ["Maglia Rosa", "2 generale", "3 generale", "Maglia ciclamino", "Maglia blu", "Maglia bianca"]
    if df.empty:
        st.write("Non hai giocato nessuno")
    elif df.shape[0] == 6:
        st.write("Hai completato la tua giocata finale")
        df = df.set_index(0)
        df.columns = ["Posizione", "Corridore", "Squadra"]
        # Define the cell editor parameters
        cell_editor_params = {
            'values': position_available
        }

        # Create a GridOptionsBuilder
        gb = GridOptionsBuilder.from_dataframe(df)

        # Configure the columns
        gb.configure_column('Posizione', cellEditor='agSelectCellEditor', cellEditorParams=cell_editor_params,
                            editable=True)
        gb.configure_column('Corridore', editable=False)
        gb.configure_column('Squadra', editable=False)
        # Build the grid options
        gridOptions = gb.build()
        # Display the DataFrame with AgGrid
        grid_return = AgGrid(df, gridOptions=gridOptions, editable=True, enable_delete=True)
        # Get the updated DataFrame
        updated_df = grid_return['data']
        # st.data_editor(updated_df)
        time.sleep(6)
        return
    else:
        st.write("La tua giocata per ora:")
        df = df.set_index(0)
        df.columns = ["Posizione", "Corridore", "Squadra"]
        # Define the cell editor parameters
        cell_editor_params = {
            'values': position_available
        }

        # Create a GridOptionsBuilder
        gb = GridOptionsBuilder.from_dataframe(df)

        # Configure the columns
        gb.configure_column('Posizione', cellEditor='agSelectCellEditor', cellEditorParams=cell_editor_params,
                            editable=True)
        gb.configure_column('Corridore', editable=False)
        gb.configure_column('Squadra', editable=False)
        gb.configure_column('Tappa', editable=False)
        # Build the grid options
        gridOptions = gb.build()
        # Display the DataFrame with AgGrid
        grid_return = AgGrid(df, gridOptions=gridOptions, editable=True, enable_delete=True)
        # Get the updated DataFrame
        updated_df = grid_return['data']
        # st.data_editor(updated_df)
    if st.button("Cancella tutte le tue giocate di giornata"):
        delete_giocata_giornata("finale", squadra)
        st.write("Giocate cancellate")
        st.rerun()
    # Search bar for rider name
    rider_name_ = st.sidebar.text_input("Cerca corridore:")
    st.write(rider_name_)
    selected_rider = None
    total_rider = pd.read_csv(r"C:\Users\it-pc-BHF8CK3\Downloads\fantagiro\venv\riders_df.csv").drop_duplicates("riders")
    total_rider["riders"] = total_rider["riders"].str.replace("-", " ")
    # Filter by team (you can customize this based on your data)
    team_filter = st.sidebar.selectbox("Filtra per squadra", ["All Teams"] + list(total_rider.team.unique()))
    # Display rider stats
    if rider_name_:
        filtered_riders = [r for n, r in total_rider.iterrows() if rider_name_.lower() in r.riders.lower()]
        if team_filter != "All Teams":
            filtered_riders = [r for r in filtered_riders if r["team"] == team_filter]
        if filtered_riders:
            selected_rider = st.sidebar.selectbox("Select a rider:", [r["riders"] for r in filtered_riders])
            #rider_stats = next((r["stats"] for r in filtered_riders if r["name"] == selected_rider), "")
            #st.write(f"Stats for {selected_rider}:\n{rider_stats}")
        else:
            st.warning("No matching riders found.")
    # Position selection
    if selected_rider:

        if not df.empty:
            position_available = [p for p in position_available if p not in list(df.Posizione.unique())]
        position = st.selectbox("Scegli posizione:", position_available)
        st.write(f"{position} - {selected_rider}")
        if position:
            if st.button("Enter rider"):
                add_rider(selected_rider, position, "finale", squadra)
                st.write(f"{selected_rider} aggiunto in posizione {position}")
                st.rerun()
    return


def read_team_user(name):
    query = f"SELECT * FROM iscritti WHERE user = '{name}'"
    df = cursor.execute(query)
    df = pd.DataFrame(df.fetchall())
    return df


def create_team_user(name, name_team):
    query = f"INSERT INTO iscritti (user, team) VALUES (?, ?)"
    cursor.execute(query, (name, name_team))
    conn.commit()
    return


# Streamlit app
def main():
    tappa = 4
    st.title("FantaGiro")
    st.sidebar.title("Fantagiro App")
    # User login
    authenticator.login()
    if st.session_state["authentication_status"]:
        st.sidebar.write(f'Welcome *{st.session_state["name"]}*')
    elif st.session_state["authentication_status"] is False:
        st.sidebar.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] is None:
        st.sidebar.warning('Please enter your username and password')

    if st.session_state["authentication_status"]:
        # Menu options
        pagine = [
                "Home",
                "Inserisci la tua squadra di giornata",
                "Le giocate di giornata",
                "Inserisci squadra finale",
                "Le giocate finali",
                "Classifica parziale",
                "Classifica rosa"
            ]
        df_user = read_team_user(st.session_state["name"])
        if df_user.empty:
            name_team = st.text_input("Nome squadra", None)
            if name_team is not None:
                st.write(name_team)
                create_team_user(st.session_state["name"], name_team)
                st.write(f"Hai creato la tua squadra: **{name_team}**")
        if not df_user.empty:
            df_user.set_index(0, inplace=True)
            df_user.columns = ["user", "team"]
            name_team = df_user['team'].iloc[0]
            menu_choice = st.sidebar.selectbox("Che vuoi fa?", pagine)
            if menu_choice == "Home":
                # Display home content
                st.image("venv/images/giro24.jpg", use_column_width=True)
                if read_giocata_giornata("finale", name_team).empty:
                    st.header("Schiera la tua squadra per la classifica finale")
            if menu_choice == "Inserisci squadra finale":
                create_team_page_final(squadra=name_team)
            elif menu_choice == "Inserisci la tua squadra di giornata":
                # Display Create Team page
                create_team_page(tappa=tappa, squadra=name_team)
            elif menu_choice == "Le giocate di giornata":
                # Display Create Team page
                vedi_giocate(tappa=tappa)
            authenticator.logout()
            if st.button("Reset Password"):
                try:
                    if authenticator.reset_password(st.session_state["username"]):
                        st.success("Password modified successfully")
                except Exception as e:
                    st.error(e)

if __name__ == "__main__":
    main()
