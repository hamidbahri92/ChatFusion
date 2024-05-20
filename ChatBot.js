import React, { useState } from "react";
import { Box, VStack, HStack, Input, Button, Text, Image, useToast } from "@chakra-ui/react";
import axios from "axios";

const ChatBot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const sendMessage = async () => {
    if (input.trim() === "" && !image) return;
    setLoading(true);

    const formData = new FormData();
    formData.append("user_message", input);
    if (image) {
      formData.append("image", image);
    }

    try {
      const response = await axios.post("/api/chat", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setMessages((prevMessages) => [
        ...prevMessages,
        { user: input, assistant: response.data.assistant_response },
      ]);
      setInput("");
      setImage(null);
    } catch (error) {
      toast({
        title: "Error",
        description: "An error occurred while processing your request.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
    setLoading(false);
  };

  const handleImageUpload = (e)### Continued Frontend Implementation

#### Complete the ChatBot Component

**فایل `ChatBot.js`** (ادامه):
```jsx
  const handleImageUpload = (e) => {
    setImage(e.target.files[0]);
  };

  return (
    <Box maxWidth="600px" margin="auto" padding={4}>
      <VStack spacing={4} align="stretch">
        <Box overflowY="auto" maxHeight="400px">
          {messages.map((msg, idx) => (
            <Box key={idx} marginBottom={4}>
              <Text fontWeight="bold">{msg.user ? "You" : "Assistant"}</Text>
              {msg.user && msg.user.startsWith("[Image]") && (
                <Image src={msg.user.slice(7)} alt="User uploaded image" />
              )}
              <Text>{msg.user ? msg.user : msg.assistant}</Text>
            </Box>
          ))}
        </Box>
        <HStack>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={loading}
          />
          <Input type="file" onChange={handleImageUpload} disabled={loading} />
          <Button onClick={sendMessage} isLoading={loading} colorScheme="blue">
            Send
          </Button>
        </HStack>
      </VStack>
    </Box>
  );
};

export default ChatBot;
