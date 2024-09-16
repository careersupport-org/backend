package org.minturtle.careersupport.interview.service;


import lombok.RequiredArgsConstructor;
import org.minturtle.careersupport.common.service.ChatService;
import org.minturtle.careersupport.interview.InterviewTemplateRepository;
import org.minturtle.careersupport.interview.dto.CreateInterviewTemplateResponse;
import org.minturtle.careersupport.interview.entity.InterviewMessage;
import org.minturtle.careersupport.interview.entity.InterviewTemplate;
import org.minturtle.careersupport.interview.repository.InterviewMessageRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;

@Service
@RequiredArgsConstructor
public class InterviewService {

    private final ChatService chatService;

    private final InterviewTemplateRepository interviewTemplateRepository;

    private final InterviewMessageRepository interviewMessageRepository;

    @Value("${spring.ai.openai.messages.interview-system-message}")
    private String interviewSystemMessage;

    @Value("${spring.ai.openai.messages.follow-system-message}")
    private String followSystemMessage;



    public Mono<CreateInterviewTemplateResponse> createTemplate(
            String userId, String theme
    ){
        InterviewTemplate interviewTemplate = InterviewTemplate.builder().userId(userId).theme(theme).build();

        return interviewTemplateRepository.save(interviewTemplate)
            .map(CreateInterviewTemplateResponse::of);
    }

    public Flux<String> getInterviewQuestion(String templateId){
        Mono<InterviewTemplate> templateMono = interviewTemplateRepository.findById(templateId);

        return templateMono.flatMapMany(template -> {
            return chatService.generate(interviewSystemMessage, template.getTheme());
        });
    }

    public Flux<String> getFollowQuestion(String theme, String previousQuestion, String previousAnswer){
        return chatService.generate(followSystemMessage, List.of(previousQuestion, previousAnswer), theme);
    }

    public Mono<Void> saveMessage(String templateId, InterviewMessage.SenderType sender, String content) {
        InterviewMessage message = InterviewMessage.builder()
                .templateId(templateId)
                .sender(sender)
                .content(content)
                .build();

        return interviewMessageRepository.save(message).then();
    }
}
