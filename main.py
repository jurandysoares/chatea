#!/usr/bin/env python3

from environs import Env
import requests
import typer

app = typer.Typer()

# Load env
env = Env()
env.read_env()
gitea_url = env.str("GITEA_URL")
gitea_token = env.str("GITEA_TOKEN")

endpoint = {
    'get_org_teams': '/api/v1/orgs/{org}/teams',
    'get_team_member': '/api/v1/teams/{id}/members/{username}',
    'get_team_members': '/api/v1/teams/{id}/members',
    'get_team_repos_org': '/api/v1/teams/{id}/repos/{org}/{repo}',
    'put_team_member': '/api/v1/teams/{id}/members/{username}',
    'get_user': '/api/v1/users/{username}',
}

AUTH_HEADERS = {
    "Authorization": f"token {gitea_token}",
    "Accept": "application/json",
}


def get_user(username: str):
    """
    Get a Gitea user by username.
    """
    url = f"{gitea_url}{endpoint['get_user'].format(username=username)}"
    response = requests.get(url, headers=AUTH_HEADERS)
    response.raise_for_status()
    return response.json()

@app.command()
def members(org: str,# = typer.Option(..., help="Gitea organization name"),
            team: str# = typer.Option(..., help="Gitea team name")
            ):
    """
    List members of a Gitea team.
    """

    # Get the list of teams in the organization
    teams_url = f"{gitea_url}{endpoint['get_org_teams'].format(org=org)}"
    response = requests.get(teams_url, headers=AUTH_HEADERS)
    response.raise_for_status()
    teams = response.json()

    # Find the team ID for the specified team name
    team_id = None
    for t in teams:
        if t['name'] == team:
            team_id = t['id']
            break

    if team_id is None:
        typer.echo(f"Team '{team}' not found in organization '{org}'.")
        raise typer.Exit(code=1)

    # Get the list of members in the specified team
    members_url = f"{gitea_url}{endpoint['get_team_members'].format(id=team_id)}"
    response = requests.get(members_url, headers=AUTH_HEADERS)
    response.raise_for_status()
    members = response.json()

    # Print the list of members
    typer.echo(f"Members of team '{team}' in organization '{org}':")
    for member in members:
        user_info = get_user(member['username'])
        typer.echo(f"- {member['username']}, {user_info.get('full_name', 'N/A').title()}, {user_info.get('email', 'N/A')}")

@app.command()
def add_member(org: str,# = typer.Option(..., help="Gitea organization name"),
               team: str,# = typer.Option(..., help="Gitea team name"),
               username: str# = typer.Option(..., help="Gitea username to add")
               ):
    """
    Add a member to a Gitea team.
    """

    # Get the list of teams in the organization
    teams_url = f"{gitea_url}{endpoint['get_org_teams'].format(org=org)}"
    response = requests.get(teams_url, headers=AUTH_HEADERS)
    response.raise_for_status()
    teams = response.json()

    # Find the team ID for the specified team name
    team_id = None
    for t in teams:
        if t['name'] == team:
            team_id = t['id']
            break

    if team_id is None:
        typer.echo(f"Team '{team}' not found in organization '{org}'.")
        raise typer.Exit(code=1)
    
    try:
        # Add the member to the specified team
        add_member_url = f"{gitea_url}{endpoint['put_team_member'].format(id=team_id, username=username)}"
        response = requests.put(add_member_url, headers=AUTH_HEADERS)
        response.raise_for_status()
        typer.echo(f"User '{username}' added to team '{team}' in organization '{org}'.")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            typer.echo(f"User '{username}' not found or cannot be added to team '{team}'.")
        else:
            typer.echo(f"Failed to add user '{username}' to team '{team}': {e}")
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == '__main__':
    main()
