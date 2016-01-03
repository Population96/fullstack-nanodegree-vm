# Python Tournament Tracker w/DB

This application was developed for the **Udacity** _Relational Database_ Class 
as part of the _Full Stack Web Developer_ Nanodegree.  Python Tournament Tracker
 _(aka PTT)_ is designed to track players in a game tournament, and 
 automatically determine the Swiss-style pairings in a single elimination 
 tournament bracket.  Players are matched up by most worthy opponent, matching
 similar win-record players.

## Software Requirements:

- [Git](https://git-scm.com/) for ease-to-use of command line.
- [Vagrant](https://www.vagrantup.com/) necessary for environment.
 
## Installation Instructions:

1. Install [Git](https://git-scm.com/).
2. Install [Vagrant](https://www.vagrantup.com/).  A restart of your computer
may be required.
3. Create a new folder in desired location for this project.
4. In this new folder, open a git bash shell by right clicking and selecting 
`Git Bash Here`.
5. Enter into the shell: `git clone https://github.com/Population96/fullstack-nanodegree-vm.git`
6. Type the command `cd fullstack-nanodegree-vm` to change directory to the base
of the project.
7. Enter `vagrant up` in the shell to tell vagrant to initiate the environment 
setup.  Vagrant will install VirtualBox and the necessary environment.
8. Once completed, enter `vagrant ssh` to login to the virtual machine.
9. The prompt will change and you are now in the virtual environment.  Enter `cd ../../vagrant/tournament` in this new prompt to reach the program's files.
10. `psql` will open the database software.
11. To build the necessary database structure needed, type `\i tournament.sql`.
12. Once the database is built, enter `\q` to exit the PostgreSQL interface.
13. Run the test case with `python tournament_test.py`
14. Exit the environment with the `exit` command.

### Functions:

- deleteMatches()
- deletePlayers()
- countPlayers()
- registerPlayer(name)
- playerStandings()
- playerStanding(id)
- reportMatch(winner, loser)
- reportMatchDraw(winner, loser)
- swissPairings()
