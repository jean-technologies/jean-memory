const { JeanClient } = require('../sdk/node/dist/index.js');

async function runNodeStressTest() {
    console.log('🟢 Node.js Stress Test Starting...');
    
    const client = new JeanClient({ 
        apiKey: 'jean_sk_f3LqQ_2KMDLlD681e7cTEHAhMyhDXdbvct-cZR6Ryrk' 
    });
    
    const results = [];
    const startTime = Date.now();
    
    // Generate chaos messages
    const messages = [
        'What do you know about me?',
        'Remember this chaos test',
        'Node.js SDK testing in progress',
        'Store this memory: Node chaos test active',
        'Retrieve my previous messages',
        'Test conversation continuity',
        'Edge case: empty response check',
        'Memory persistence verification'
    ];
    
    // Add random messages
    for (let i = 0; i < 100; i++) {
        messages.push(`Random chaos message ${i}: ${Math.random().toString(36)}`);
    }
    
    // Run tests concurrently
    const concurrency = 10;
    const batches = [];
    
    for (let batch = 0; batch < 10; batch++) {
        const batchPromises = [];
        
        for (let i = 0; i < concurrency; i++) {
            const messageIndex = (batch * concurrency + i) % messages.length;
            const message = messages[messageIndex];
            
            const testPromise = (async () => {
                const testStart = Date.now();
                try {
                    const response = await client.getContext({
                        user_token: 'mock_jwt_token',
                        message: message,
                        is_new_conversation: Math.random() > 0.7
                    });
                    
                    return {
                        success: true,
                        duration: Date.now() - testStart,
                        responseSize: response.text.length,
                        batch: batch,
                        index: i
                    };
                } catch (error) {
                    return {
                        success: false,
                        duration: Date.now() - testStart,
                        error: error.message,
                        batch: batch,
                        index: i
                    };
                }
            })();
            
            batchPromises.push(testPromise);
        }
        
        console.log(`🔥 Launching batch ${batch + 1}/10 with ${concurrency} concurrent requests...`);
        const batchResults = await Promise.all(batchPromises);
        results.push(...batchResults);
        
        // Brief pause between batches
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Generate report
    const totalDuration = Date.now() - startTime;
    const successCount = results.filter(r => r.success).length;
    const failCount = results.length - successCount;
    const avgDuration = results.reduce((sum, r) => sum + r.duration, 0) / results.length;
    const avgResponseSize = results.filter(r => r.responseSize)
        .reduce((sum, r) => sum + r.responseSize, 0) / 
        Math.max(1, results.filter(r => r.responseSize).length);
    
    console.log(`
╔════════════════════════════════════════════════════════════════════════════╗
║                        🟢 NODE.JS CHAOS REPORT 🟢                         ║
╚════════════════════════════════════════════════════════════════════════════╝

⏱️  Total Duration: ${totalDuration}ms
🎯 Total Tests: ${results.length}
✅ Successful: ${successCount} (${(successCount/results.length*100).toFixed(1)}%)
❌ Failed: ${failCount} (${(failCount/results.length*100).toFixed(1)}%)
📊 Avg Response Time: ${avgDuration.toFixed(0)}ms
📏 Avg Response Size: ${avgResponseSize.toFixed(0)} characters
🚀 Requests Per Second: ${(results.length / (totalDuration/1000)).toFixed(1)} RPS

${successCount > results.length * 0.8 ? '🎉 NODE.JS SDK SURVIVED THE CHAOS!' : '⚠️  NODE.JS SDK NEEDS ATTENTION'}
    `);
    
    // Save detailed results
    const fs = require('fs');
    const reportPath = `./logs/node_stress_report_${Date.now()}.json`;
    fs.writeFileSync(reportPath, JSON.stringify({
        metadata: {
            totalDuration,
            totalTests: results.length,
            successRate: successCount / results.length,
            avgDuration,
            avgResponseSize
        },
        results
    }, null, 2));
    
    console.log(`📄 Detailed report saved: ${reportPath}`);
}

runNodeStressTest().catch(console.error);
