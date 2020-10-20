package threeChess;

import java.io.*;
import java.util.*;

import threeChess.agents.*;

/**
 * Class with static methods for running tournaments and playing threeChess matches.
 * @author Tim French
 * **/
public class ThreeChess{

  private final static int pause = 1000;//The pause in milliseconds between updating the graphical board
  private final static int[][] perms = {{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};//to randomise play order
  private final static Random random = new Random();
  
  /**
   * A private class for representing the statistics of an agent in a tournament.
   * **/
  private static class Statistics implements Comparable{
    private int won;
    private int lost;
    private int pass;
    private int played;
    private Agent agent;

    /**
     * Constructs a statistics object for the given agent
     * **/
    public Statistics(Agent a){agent = a;}

    /**
     * Updates the Statistics objects with the score from a game.
     * @param score -2 if an illegal move is attempt, -1 for a loss, 0 for a draw and +1 for a win.
     * **/
    public void update(int score){
      switch(score){
        case -2: lost+=2; break;
        case -1: lost++;break;
        case 0: pass++;break;
        case 1: won++; break;
        default:
      }
      played++;
    }

    /**
     * @return the average score of the player
     * **/
    public double average(){return (1.0*(won-lost))/played;}

    /**
     * @return a JSON representation of the Statistics for an agent.
     * **/
    public String toString(){return "name:"+ agent+", won:"+won+", lost:"+lost+", played:"+played+", avg:"+average();}

    /**
     * @param o the object to compare to.
     * @return -1 if this object has a higher average than the paramater, 0 if the averages are equivalent and +1 if it has a lower average score.
     * **/
    public int compareTo(Object o){
      if(o instanceof Statistics){
        Statistics stats = (Statistics) o;
        return Double.compare(stats.average(), average());
      } else return -1;
    }
  }



  /**
   * Runs a tournament for a group of agents.
   * The games in the tournament will have the specified time limit.
   * If a non-zero number of games are specified, the agents will be randomly assigned to games.
   * If 0 is specified, every agent will play every other pair of agents, with the colours of the pieces randomly assigned.
   * @param bots an array of Agents to compete in the contest.
   * @param timeLimit the cumulative time each player has (in seconds). To specify an untimed game, set as less than or equal to zero.
   * @param displayOn a boolean flag for whether the game should be graphically displayed
   * @param logFile a FileName to print the game logs to. If this can't be found, or is null, System.out will be used instead.
   * **/
  public static void  tournament(Agent[] bots, int timeLimit, int numGames, Boolean displayOn, String logFile){
    HashMap<Agent, Statistics> scoreboard = new HashMap<Agent,Statistics>();
    PrintStream logger = System.out;
    try{
      if(logFile!=null) logger = new PrintStream(new File(logFile));
    }
    catch(IOException e){System.out.println(logFile+"not found: "+e.getMessage()+"\nUsing System.out instead.");}
    for(Agent a: bots) scoreboard.put(a, new Statistics(a));
    if(numGames==0){//all combinations of three agents play each other. In each game the order is random.
      for(int i = 0; i<bots.length; i++){
        for(int j = i+1; j<bots.length; j++){
          for(int k = j+1; k<bots.length; k++){
            int[] players = {i,j,k};
            int[] ord = perms[random.nextInt(perms.length)];
            int[] res = play(bots[players[ord[0]]],bots[players[ord[1]]],bots[players[ord[2]]], timeLimit, logger, displayOn);
            for(int o = 0; o<3;o++)scoreboard.get(bots[players[ord[o]]]).update(res[o]);
          }
        }
      }
    }
    else{//play randomly assigned games. Note agents may play themselves.
      int n = bots.length;
      for(int g = 0; g<numGames; g++){
        int[] players = {random.nextInt(n), random.nextInt(n), random.nextInt(n)};
        int[] res = play(bots[players[0]],bots[players[1]],bots[players[2]], timeLimit, logger, displayOn);
        for(int o = 0; o<3;o++)scoreboard.get(bots[players[o]]).update(res[o]);
      }
    }
    for(Agent a: bots)logger.println(scoreboard.get(a));
    logger.println("Rank\tAgent\t\tWon\tLost\tPlayed\tAvg\n");
    Statistics[] results = (Statistics[]) scoreboard.values().toArray(new Statistics[0]);
    Arrays.sort(results);
    int rank = 1;
    for(Statistics stat:results)
      logger.println(rank++ +"\t"+stat.agent+"\t\t"+stat.won+"\t"+stat.lost+"\t"+stat.played+"\t"+stat.average()+"\n");
  }
  
  /**
   * Runs a threeChess game between three players.
   * There are options to display the board, and log the game to a text file.
   * A time limit may also be specified for a timed game.
   * @param blue the agent playing the blue pieces.
   * @param green the agent playing the green pieces.
   * @param red the Agent playing the red pieces.
   * @param timeLimit the cumulative time each player has (in seconds). To specify an untimed game, set as less than or equal to zero.
   * @param logger a printStream to write the game moves to.
   * @param displayOn a boolean flag for whether the game should be graphically displayed
   * @return an array of three ints, the scores for blue, green and red, in that order.
   * **/
  public static int[] play(Agent blue, Agent green, Agent red, int timeLimit, PrintStream logger, boolean displayOn){
    Agent[] agents = {blue, green, red};
    Game game = new Game(agents, timeLimit, 0, pause, logger, displayOn);
    game.run();
    return game.getAgentScores();
  }

  /**
   * Runs a timed threeChess game between three players
   * with a graphical board and moves logged to System.out.
   * @param blue the agent playing the blue pieces.
   * @param green the agent playing the green pieces.
   * @param red the agent playing the red pieces.
   * @return an array of three ints, the scores for blue, green and red, in that order.
   * **/
  public static int[] play(Agent blue, Agent green, Agent red){
    return play(blue, green, red, 0, System.out, true);
  }
  
  /**
   * Default play scenario for three manual agents, no time limit,
   * logged to System.out with display on.
   * **/
  public static void play(){
    Agent man  = new ManualAgent();
    play(man, man, man);
  }


  /** 
   * This plays a manual game where all rules are ignored.
   * This effectively allows you to move pieces around the board for simulating positions.
   * **/
  public static void playCheat(){
    Board board = new CheatBoard();
    Agent agent = new ManualAgent();
    ThreeChessDisplay display = new ThreeChessDisplay(board, "Blue", "Green", "Red");
    while(!board.gameOver()){//note in an untimed game, this loop can run infinitely.
      Position[] move = null;
      try{
        move = agent.playMove((Board) board.clone());
      }catch(CloneNotSupportedException e){}
      if(move!=null && move.length==2){
        try{
          board.move(move[0],move[1],0);
          display.repaintCanvas();
        }
        catch(ImpossiblePositionException e){System.out.println(e.getMessage());}
      }
    }
  }


  /**
   * This method can be customised to run tournaments with agents added in the code (add them to array bots), 
   * or manual games between players, or a cheat mode which is effectively a board that can be freely manipulated.
   * Run program with parameter "manual" for a game with moves added in the command line, "cheat" to ignore all rules, and no parameters to run a tournament between agents listed in bots.
   **/
  public static void main(String[] args){
    Agent[] bots = {new RandomAgent(), new RandomAgent(), new RandomAgent()};
    if(args.length > 0 && args[0].equals("manual")){
      bots = new Agent[] {new ManualAgent("A"), new ManualAgent("B"), new ManualAgent("C")};
      tournament(bots,60,0,true, null);
    }
    else if(args.length > 0 && args[0].equals("gui")){
      bots = new Agent[] {new GUIAgent("A"), new GUIAgent("B"), new GUIAgent("C")};
      tournament(bots,60,0,true, null);
    }
    else if (args.length > 0 && args[0].equals("cheat")){
      playCheat();
    }
    else if (args.length > 0 && args[0].equals("tournament")) {
      bots = new Agent[] {new RandomAgent(), new RandomAgent(), new RandomAgent(), new RandomAgent()};
      Tournament tournament = new Tournament(
              bots, // agents
              10_000, // numGames
              10, // timeLimitSeconds
              300, // maximumTurns
              0, // pauseMS
              Runtime.getRuntime().availableProcessors(), // threads
              System.out, // logger
              false
      );
      tournament.runTournament();
    }
    else tournament(bots,300,0,true,null);
  }
}
