package threeChess;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Helper class for formatting the board state for LLM consumption
 */
public class BoardFormatter {
    
    /**
     * Formats the current board state as a string for the LLM
     * @param board The current board state
     * @return A string representation of the board suitable for LLM analysis
     */
    public static String formatBoardState(Board board) {
        StringBuilder sb = new StringBuilder();
        
        // Add whose turn it is
        sb.append("Current turn: ").append(board.getTurn()).append("\n\n");
        
        // Add time information for each player
        sb.append("Time remaining:\n");
        for (Colour colour : Colour.values()) {
            int timeMs = board.getTimeLeft(colour);
            double timeSec = timeMs / 1000.0;
            sb.append(colour).append(" time: ").append(timeMs).append(" ms (").append(String.format("%.1f", timeSec)).append(" seconds)\n");
        }
        sb.append("\n");
        
        // Add pieces for each color
        for (Colour colour : Colour.values()) {
            sb.append(colour).append(" pieces:\n");
            Set<Position> positions = board.getPositions(colour);
            for (Position pos : positions) {
                Piece piece = board.getPiece(pos);
                if (piece != null) {
                    sb.append(pos).append(": ").append(pieceTypeToChar(piece.getType())).append("\n");
                }
            }
            sb.append("\n");
        }
        
        // Add captured pieces
        sb.append("Captured pieces:\n");
        for (Colour colour : Colour.values()) {
            sb.append(colour).append(" captured: ");
            List<Piece> captured = board.getCaptured(colour);
            if (captured != null && !captured.isEmpty()) {
                for (Piece piece : captured) {
                    sb.append(pieceTypeToChar(piece.getType())).append(" ");
                }
            } else {
                sb.append("None");
            }
            sb.append("\n");
        }
        
        return sb.toString();
    }
    
    /**
     * Formats the move history as a string for the LLM
     * @param board The current board with history
     * @return A string representation of the move history
     */
    public static String formatMoveHistory(Board board) {
        StringBuilder sb = new StringBuilder();
        
        // Since board.getHistory() doesn't exist, we'll create our own history format
        // based on what we can access
        sb.append("No detailed move history available.\n");
        
        return sb.toString();
    }
    
    /**
     * Gets all legal moves for the current player
     * @param board The current board state
     * @return A string listing all legal moves
     */
    public static String getLegalMoves(Board board) {
        StringBuilder sb = new StringBuilder();
        Colour turn = board.getTurn();
        
        Set<Position> positions = board.getPositions(turn);
        ArrayList<String> legalMoves = new ArrayList<>();
        
        for (Position start : positions) {
            for (Position end : getAllSquares()) {
                if (board.isLegalMove(start, end)) {
                    legalMoves.add(start + " to " + end);
                }
            }
        }
        
        // Add a clear header with the count of legal moves
        sb.append("=== LEGAL MOVES FOR ").append(turn).append(" (").append(legalMoves.size()).append(" moves) ===\n");
        
        // Number each move for clarity
        for (int i = 0; i < legalMoves.size(); i++) {
            sb.append(i + 1).append(". ").append(legalMoves.get(i)).append("\n");
        }
        
        // Add a footer to make it clearer
        sb.append("=== END OF LEGAL MOVES LIST ===\n");
        
        return sb.toString();
    }
    
    /**
     * Helper method to get all possible board positions
     * @return Set of all positions on the board
     */
    private static Set<Position> getAllSquares() {
        Set<Position> squares = new HashSet<>();
        try {
            for (Colour c : Colour.values()) {
                for (int i = 0; i < 8; i++) {
                    for (int j = 0; j < 8; j++) {
                        squares.add(Position.get(c, i, j));
                    }
                }
            }
        } catch (ImpossiblePositionException e) {
            // This shouldn't happen with valid board coordinates
        }
        return squares;
    }
    
    /**
     * Converts piece type to character representation
     * @param type The piece type
     * @return Character representation (K, Q, R, B, N, P)
     */
    private static char pieceTypeToChar(PieceType type) {
        switch (type) {
            case KING: return 'K';
            case QUEEN: return 'Q';
            case ROOK: return 'R';
            case BISHOP: return 'B';
            case KNIGHT: return 'N';
            case PAWN: return 'P';
            default: return '?';
        }
    }
} 