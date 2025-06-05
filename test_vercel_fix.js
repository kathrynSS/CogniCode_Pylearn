// Vercel修复验证脚本
// 在浏览器控制台运行此脚本来测试修复效果

(function() {
    console.log('🔧 开始验证Vercel修复效果...');
    
    async function testProjectsAPIFixed() {
        try {
            console.log('📊 测试项目API修复...');
            
            const response = await fetch('/api/projects');
            console.log('API响应状态:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('API响应数据:', data);
            
            if (data.success) {
                const projectCount = Object.keys(data.projects || {}).length;
                const templateCount = Object.values(data.projects || {}).filter(p => p.type === 'template').length;
                const userCount = Object.values(data.projects || {}).filter(p => p.type === 'user_created').length;
                
                console.log('✅ API调用成功！');
                console.log(`📁 总项目数: ${projectCount}`);
                console.log(`📚 模板项目: ${templateCount}`);
                console.log(`👤 用户项目: ${userCount}`);
                
                if (data.debug) {
                    console.log('🐛 调试信息:', data.debug);
                    if (data.debug.errors && data.debug.errors.length > 0) {
                        console.warn('⚠️ 发现错误:', data.debug.errors);
                    } else {
                        console.log('✅ 没有发现错误');
                    }
                }
                
                return true;
            } else {
                console.error('❌ API返回失败:', data.error);
                return false;
            }
            
        } catch (error) {
            console.error('❌ API调用失败:', error);
            return false;
        }
    }
    
    async function testAuthAndProjects() {
        try {
            console.log('🔐 检查认证状态...');
            
            const authResponse = await fetch('/api/auth/check');
            const authData = await authResponse.json();
            
            console.log('认证状态:', authData.authenticated);
            
            if (authData.authenticated) {
                console.log('✅ 用户已登录，用户项目应该显示');
                console.log('用户信息:', authData.user);
            } else {
                console.log('⚠️ 用户未登录，只显示模板项目');
                console.log('💡 要看到用户项目，请先登录');
            }
            
            return authData.authenticated;
            
        } catch (error) {
            console.error('❌ 认证检查失败:', error);
            return false;
        }
    }
    
    async function simulateDropdownLoad() {
        try {
            console.log('🔄 模拟项目下拉栏加载...');
            
            const response = await fetch('/api/projects');
            const data = await response.json();
            
            if (data.success) {
                // 模拟前端下拉栏逻辑
                const templateProjects = {};
                const userProjects = {};
                
                Object.entries(data.projects).forEach(([id, project]) => {
                    if (project.type === 'template') {
                        templateProjects[id] = project;
                    } else {
                        userProjects[id] = project;
                    }
                });
                
                console.log('📚 模拟下拉栏 - 模板项目:');
                Object.entries(templateProjects).forEach(([id, project]) => {
                    console.log(`  - ${project.name} (${project.total_steps} 步)`);
                });
                
                if (Object.keys(userProjects).length > 0) {
                    console.log('👤 模拟下拉栏 - 用户项目:');
                    Object.entries(userProjects).forEach(([id, project]) => {
                        console.log(`  - ${project.name} (${project.total_steps} 步)`);
                    });
                } else {
                    console.log('👤 没有用户项目（可能因为未登录或没有创建项目）');
                }
                
                return true;
            } else {
                console.error('❌ 项目数据加载失败:', data.error);
                return false;
            }
            
        } catch (error) {
            console.error('❌ 下拉栏模拟失败:', error);
            return false;
        }
    }
    
    async function runFixValidation() {
        console.log('🚀 开始验证修复效果...');
        console.log('================================');
        
        // 1. 测试认证状态
        const isAuthenticated = await testAuthAndProjects();
        console.log('================================');
        
        // 2. 测试项目API
        const apiWorking = await testProjectsAPIFixed();
        console.log('================================');
        
        // 3. 模拟下拉栏加载
        const dropdownWorking = await simulateDropdownLoad();
        console.log('================================');
        
        // 总结
        console.log('📋 修复验证总结:');
        console.log(`✓ API正常工作: ${apiWorking ? '是' : '否'}`);
        console.log(`✓ 用户已认证: ${isAuthenticated ? '是' : '否'}`);
        console.log(`✓ 下拉栏模拟: ${dropdownWorking ? '成功' : '失败'}`);
        
        if (apiWorking && dropdownWorking) {
            console.log('🎉 修复成功！项目下拉栏应该正常工作了');
            console.log('💡 如果问题仍然存在，请刷新页面重试');
        } else {
            console.log('⚠️ 仍有问题，请查看上面的详细错误信息');
        }
        
        console.log('🔍 修复验证完成');
    }
    
    // 导出到全局
    window.testVercelFix = {
        testAPI: testProjectsAPIFixed,
        testAuth: testAuthAndProjects,
        testDropdown: simulateDropdownLoad,
        runAll: runFixValidation
    };
    
    // 自动运行验证
    runFixValidation();
    
    console.log('💡 你也可以使用 window.testVercelFix.functionName() 单独测试功能');
})(); 