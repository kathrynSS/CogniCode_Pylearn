// Vercel部署调试脚本
// 在浏览器控制台运行此脚本来诊断问题

(function() {
    console.log('🔍 开始Vercel部署诊断...');
    
    // 1. 检查认证状态
    async function checkAuthStatus() {
        try {
            console.log('📋 检查认证状态...');
            const response = await fetch('/api/auth/check');
            const data = await response.json();
            console.log('认证状态:', data);
            return data;
        } catch (error) {
            console.error('❌ 认证检查失败:', error);
            return null;
        }
    }
    
    // 2. 检查项目API
    async function checkProjectsAPI() {
        try {
            console.log('📋 检查项目API...');
            const response = await fetch('/api/projects');
            console.log('Projects API响应状态:', response.status);
            console.log('Projects API响应头:', Object.fromEntries(response.headers.entries()));
            
            if (response.ok) {
                const data = await response.json();
                console.log('Projects API数据:', data);
                return data;
            } else {
                const text = await response.text();
                console.error('❌ Projects API错误响应:', text);
                return null;
            }
        } catch (error) {
            console.error('❌ Projects API调用失败:', error);
            return null;
        }
    }
    
    // 3. 检查数据库连接
    async function checkDatabaseConnection() {
        try {
            console.log('📋 尝试测试数据库连接...');
            const response = await fetch('/api/user/statistics');
            console.log('数据库测试响应状态:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('✅ 数据库连接正常:', data);
                return true;
            } else {
                const text = await response.text();
                console.log('⚠️ 数据库连接可能有问题:', text);
                return false;
            }
        } catch (error) {
            console.error('❌ 数据库连接测试失败:', error);
            return false;
        }
    }
    
    // 4. 检查环境信息
    function checkEnvironment() {
        console.log('📋 环境信息:');
        console.log('- URL:', window.location.href);
        console.log('- Host:', window.location.host);
        console.log('- Protocol:', window.location.protocol);
        console.log('- User Agent:', navigator.userAgent);
        console.log('- Local Storage Keys:', Object.keys(localStorage));
        console.log('- Session Storage Keys:', Object.keys(sessionStorage));
        
        // 检查Cookies
        const cookies = document.cookie.split(';').map(c => c.trim()).filter(c => c);
        console.log('- Cookies:', cookies);
    }
    
    // 5. 模拟项目创建测试
    async function testProjectCreation() {
        try {
            console.log('📋 测试项目创建...');
            const response = await fetch('/api/create_project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: 'Test Project - ' + new Date().toISOString(),
                    description: 'This is a test project to verify API functionality'
                })
            });
            
            console.log('创建项目响应状态:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('✅ 项目创建成功:', data);
                return data;
            } else {
                const text = await response.text();
                console.error('❌ 项目创建失败:', text);
                return null;
            }
        } catch (error) {
            console.error('❌ 项目创建测试失败:', error);
            return null;
        }
    }
    
    // 运行所有诊断
    async function runDiagnostics() {
        console.log('🚀 开始完整诊断...');
        console.log('================================');
        
        // 环境检查
        checkEnvironment();
        console.log('================================');
        
        // 认证检查
        const authStatus = await checkAuthStatus();
        console.log('================================');
        
        // 项目API检查
        const projectsData = await checkProjectsAPI();
        console.log('================================');
        
        // 数据库检查
        const dbConnected = await checkDatabaseConnection();
        console.log('================================');
        
        // 项目创建测试（仅在已认证时）
        if (authStatus && authStatus.authenticated) {
            await testProjectCreation();
            console.log('================================');
        }
        
        // 总结
        console.log('📊 诊断总结:');
        console.log('- 用户已认证:', authStatus?.authenticated || false);
        console.log('- 项目API可用:', !!projectsData);
        console.log('- 数据库连接:', dbConnected);
        
        if (projectsData) {
            console.log('- 模板项目数量:', Object.values(projectsData.projects || {}).filter(p => p.type === 'template').length);
            console.log('- 用户项目数量:', Object.values(projectsData.projects || {}).filter(p => p.type === 'user_created').length);
        }
        
        // 建议
        console.log('🎯 问题诊断建议:');
        
        if (!authStatus?.authenticated) {
            console.log('⚠️ 用户未登录 - 用户创建的项目不会显示');
            console.log('💡 建议: 确保用户已登录再检查项目列表');
        }
        
        if (!dbConnected) {
            console.log('❌ 数据库连接失败 - 用户项目无法加载');
            console.log('💡 建议: 检查Vercel环境变量中的数据库配置');
        }
        
        if (!projectsData) {
            console.log('❌ 项目API失败 - 无法获取项目列表');
            console.log('💡 建议: 检查API路由和服务器状态');
        }
        
        if (projectsData && !projectsData.success) {
            console.log('⚠️ 项目API返回错误:', projectsData.error || '未知错误');
        }
        
        console.log('🔍 诊断完成！');
        console.log('如果问题仍然存在，请将以上信息提供给开发者');
    }
    
    // 导出函数到全局，方便单独调用
    window.vercelDebug = {
        checkAuth: checkAuthStatus,
        checkProjects: checkProjectsAPI,
        checkDatabase: checkDatabaseConnection,
        checkEnvironment: checkEnvironment,
        testCreate: testProjectCreation,
        runAll: runDiagnostics
    };
    
    // 自动运行诊断
    runDiagnostics();
    
    console.log('💡 提示: 你可以使用 window.vercelDebug.functionName() 单独运行任何诊断功能');
})(); 