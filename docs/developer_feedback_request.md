# Jean Memory Integration Feedback

Hello!

Thank you for building with Jean Memory. We're currently working to improve the developer experience, especially around our longer-running AI reasoning tools like `sendMessage` and `getContext`.

Your feedback is critical to help us understand the real-world challenges and design a solution that makes integration as simple and seamless as possible.

Could you please take a few minutes to answer the following questions? Code snippets are especially helpful!

---

### 1. Your Current Implementation

Could you share a simplified code snippet of how you are currently calling the Jean Memory tool? (e.g., your Next.js API route, a frontend component function, etc.).

*(Please paste your code here)*

```javascript
// Example:
export default async function handler(req, res) {
  const context = await jean.getContext({
    user_token: userToken,
    message: req.body.query
  });

  // Then, call an LLM with the context...
  const llmResponse = await openai.chat.completions.create({...});
  
  res.json(llmResponse);
}
```

---

### 2. The Problem You're Experiencing

Could you describe the specific issue you're running into? 

-   Is the request timing out? 
-   Is the UI freezing? 
-   Are you seeing specific errors?
-   What are the typical response times you're seeing from the Jean Memory tool?

*(Your description here)*

---

### 3. Your Biggest Pain Point

If you could change **one thing** about how you use this slow function to make your life easier, what would it be?

*(Your answer here)*

---

### 4. Your Ideal Solution

In a perfect world, how would you want this function to work? Don't worry about technical limitations, just describe your ideal developer experience.

*(Your description of the ideal experience here)*

```javascript
// Example of an ideal experience:
// const result = await jean.getContext(query, {
//   timeout: 60000,
//   onProgress: (stage) => console.log(`AI is now ${stage}...`) 
// });
```

---

Thank you again for your time and valuable input. Your feedback will directly shape the future of our SDKs.
