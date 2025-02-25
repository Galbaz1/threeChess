package threeChess;

import threeChess.agents.*;
import java.util.*;
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;

/**
 * A simple launcher for ThreeChess with LLM agents.
 * This provides a UI to select different LLM models for each player.
 */
public class LLMChessLauncher {

    private static final String[] PROVIDERS = {"openai", "anthropic", "openrouter", "groq"};
    private static final String[] OPENAI_MODELS = {"gpt-4o", "gpt-4o-mini"};
    private static final String[] ANTHROPIC_MODELS = {"claude-3-5-sonnet-latest", "claude-3-opus-20240229"};
    private static final String[] OPENROUTER_MODELS = {"google/gemini-flash-1.5-8b", "mistralai/mistral-7b-instruct-v0.2"};
    private static final String[] GROQ_MODELS = {"llama-3.3-70b-versatile", "llama-3.1-8b-instant"};

    private static Map<String, String[]> PROVIDER_MODELS = new HashMap<>();
    
    static {
        PROVIDER_MODELS.put("openai", OPENAI_MODELS);
        PROVIDER_MODELS.put("anthropic", ANTHROPIC_MODELS);
        PROVIDER_MODELS.put("openrouter", OPENROUTER_MODELS);
        PROVIDER_MODELS.put("groq", GROQ_MODELS);
    }

    public static void main(String[] args) {
        // Create UI for model selection
        JFrame frame = new JFrame("ThreeChess LLM Arena");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setLayout(new BorderLayout());
        
        JPanel selectionPanel = new JPanel(new GridLayout(4, 2, 10, 10));
        selectionPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        // Blue player selection
        JComboBox<String> blueProviderCombo = new JComboBox<>(PROVIDERS);
        JComboBox<String> blueModelCombo = new JComboBox<>(OPENAI_MODELS);
        
        // Green player selection
        JComboBox<String> greenProviderCombo = new JComboBox<>(PROVIDERS);
        JComboBox<String> greenModelCombo = new JComboBox<>(ANTHROPIC_MODELS);
        greenProviderCombo.setSelectedItem("anthropic");
        
        // Red player selection
        JComboBox<String> redProviderCombo = new JComboBox<>(PROVIDERS);
        JComboBox<String> redModelCombo = new JComboBox<>(OPENROUTER_MODELS);
        redProviderCombo.setSelectedItem("openrouter");
        
        // Add listeners to update model options when provider changes
        blueProviderCombo.addActionListener(e -> {
            String provider = (String) blueProviderCombo.getSelectedItem();
            blueModelCombo.setModel(new DefaultComboBoxModel<>(PROVIDER_MODELS.get(provider)));
        });
        
        greenProviderCombo.addActionListener(e -> {
            String provider = (String) greenProviderCombo.getSelectedItem();
            greenModelCombo.setModel(new DefaultComboBoxModel<>(PROVIDER_MODELS.get(provider)));
        });
        
        redProviderCombo.addActionListener(e -> {
            String provider = (String) redProviderCombo.getSelectedItem();
            redModelCombo.setModel(new DefaultComboBoxModel<>(PROVIDER_MODELS.get(provider)));
        });
        
        // Add components to panel
        selectionPanel.add(new JLabel("Blue Player:"));
        JPanel bluePanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        bluePanel.add(blueProviderCombo);
        bluePanel.add(blueModelCombo);
        selectionPanel.add(bluePanel);
        
        selectionPanel.add(new JLabel("Green Player:"));
        JPanel greenPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        greenPanel.add(greenProviderCombo);
        greenPanel.add(greenModelCombo);
        selectionPanel.add(greenPanel);
        
        selectionPanel.add(new JLabel("Red Player:"));
        JPanel redPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        redPanel.add(redProviderCombo);
        redPanel.add(redModelCombo);
        selectionPanel.add(redPanel);
        
        // Start button
        JButton startButton = new JButton("Start Game");
        startButton.addActionListener(e -> {
            frame.setVisible(false);
            
            // Create LLM agents
            Agent blueAgent = new LLMAgent(
                (String) blueProviderCombo.getSelectedItem(),
                (String) blueModelCombo.getSelectedItem()
            );
            
            Agent greenAgent = new LLMAgent(
                (String) greenProviderCombo.getSelectedItem(),
                (String) greenModelCombo.getSelectedItem()
            );
            
            Agent redAgent = new LLMAgent(
                (String) redProviderCombo.getSelectedItem(),
                (String) redModelCombo.getSelectedItem()
            );
            
            // Start the game
            System.out.println("Starting game with the following agents:");
            System.out.println("Blue: " + blueAgent);
            System.out.println("Green: " + greenAgent);
            System.out.println("Red: " + redAgent);
            
            // Need to use the play method with a 10-second time limit per move
            ThreeChess.play(blueAgent, greenAgent, redAgent, 10000, System.out, true);
            
            // Close the application when the game is done
            System.exit(0);
        });
        
        selectionPanel.add(new JLabel(""));
        selectionPanel.add(startButton);
        
        // Add note about Python server
        JPanel notePanel = new JPanel();
        notePanel.add(new JLabel("<html><b>Note:</b> Make sure the Python server is running first: <code>python llm_server.py</code></html>"));
        
        frame.add(selectionPanel, BorderLayout.CENTER);
        frame.add(notePanel, BorderLayout.SOUTH);
        
        frame.pack();
        frame.setSize(600, 250);
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
    }
} 